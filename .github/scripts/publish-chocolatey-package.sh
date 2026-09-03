#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 <version> <nupkg-path>" >&2
  exit 1
}

VERSION="${1:-}"
NUPKG="${2:-}"
PACKAGE_ID="duplicate-finder"
PUSH_SOURCE="https://push.chocolatey.org/api/v2/package"
PACKAGE_URL="https://community.chocolatey.org/packages/${PACKAGE_ID}"
FEED_URL="https://community.chocolatey.org/api/v2/Packages?\$filter=Id%20eq%20'${PACKAGE_ID}'&\$orderby=Published%20desc&\$top=20"

if [[ -z "${VERSION}" || -z "${NUPKG}" ]]; then
  usage
fi

if [[ ! -f "${NUPKG}" ]]; then
  echo "Package not found: ${NUPKG}" >&2
  exit 1
fi

if [[ -z "${CHOCOLATEY_API_KEY:-}" ]]; then
  echo "CHOCOLATEY_API_KEY is required" >&2
  exit 1
fi

fetch_recent_versions_feed() {
  curl -fsSL "${FEED_URL}" 2>/dev/null || true
}

find_moderation_block() {
  local feed="$1"

  if [[ -z "${feed}" ]]; then
    return 1
  fi

  FEED="${feed}" perl -0777 -ne '
    my @entries;
    for my $entry (split(/<entry>/, $_)) {
      next unless $entry =~ /<\/entry>/;
      my ($version) = $entry =~ /<d:Version>([^<]+)<\/d:Version>/;
      my ($status) = $entry =~ /<d:PackageSubmittedStatus>([^<]+)<\/d:PackageSubmittedStatus>/;
      my ($approved) = $entry =~ /<d:IsApproved m:type="Edm.Boolean">([^<]+)<\/d:IsApproved>/;
      push @entries, {
        version  => $version // "",
        status   => $status // "",
        approved => ($approved // "") eq "true",
      };
    }

    for my $entry (@entries) {
      next unless $entry->{status} eq "Pending" || $entry->{status} eq "Waiting";
      print "$entry->{version}|$entry->{status}\n";
      exit 0;
    }

    my $has_approved = grep { $_->{approved} } @entries;
    if (!$has_approved && @entries) {
      print "none|no-approved-versions\n";
      exit 0;
    }
  '
}

report_moderation_block() {
  local block_version="$1"
  local block_status="$2"

  if [[ "${block_version}" == "none" && "${block_status}" == "no-approved-versions" ]]; then
    echo "::error title=Chocolatey moderation queue::Push blocked: ${PACKAGE_ID} has no approved versions on chocolatey.org yet. The community repository rejects new pushes with HTTP 403 until at least one version passes moderation. Open ${PACKAGE_URL}#versionhistory and re-run this job after approval." >&2
    return
  fi

  echo "::error title=Chocolatey moderation queue::Push blocked: ${PACKAGE_ID} ${block_version} is still in moderation (PackageSubmittedStatus=${block_status}). chocolatey.org returns HTTP 403 for new versions until it is approved. Open ${PACKAGE_URL}/${block_version} and re-run this job after approval." >&2
}

check_moderation_block() {
  local feed block_info block_version block_status

  feed="$(fetch_recent_versions_feed)"
  block_info="$(find_moderation_block "${feed}" || true)"
  if [[ -z "${block_info}" ]]; then
    return 1
  fi

  block_version="${block_info%%|*}"
  block_status="${block_info#*|}"
  report_moderation_block "${block_version}" "${block_status}"
  return 0
}

if check_moderation_block; then
  exit 1
fi

PUSH_LOG="$(mktemp)"
trap 'rm -f "${PUSH_LOG}"' EXIT

if nuget push "${NUPKG}" \
  -ApiKey "${CHOCOLATEY_API_KEY}" \
  -Source "${PUSH_SOURCE}" \
  -SkipDuplicate 2>&1 | tee "${PUSH_LOG}"; then
  exit 0
fi

if grep -q '403' "${PUSH_LOG}" || grep -qi 'Forbidden' "${PUSH_LOG}"; then
  if check_moderation_block; then
    exit 1
  fi

  echo "::error title=Chocolatey push forbidden (HTTP 403)::nuget push was rejected by chocolatey.org. This is not HTTP 409 (duplicate version). Common causes: invalid CHOCOLATEY_API_KEY, not a package maintainer, or a previous version still in moderation. Check ${PACKAGE_URL}#versionhistory" >&2
  exit 1
fi

echo "Chocolatey push failed:"
cat "${PUSH_LOG}" >&2
exit 1
