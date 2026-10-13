#!/usr/bin/env bash
# Print a BREAKING.md section scaffold (layout rules: templates/BREAKING-SECTION.md).
#
# Usage:
#   bash .cursor/skills/release-plan/scripts/scaffold-breaking-section.sh
#   bash .cursor/skills/release-plan/scripts/scaffold-breaking-section.sh --version 2.3.0 --out .cursor/skills/release-plan/.cache/breaking-2.3.0.md
#   bash .cursor/skills/release-plan/scripts/scaffold-breaking-section.sh --from 2.2.0 --to 2.3.0 --pr 42
#
# FROM/TO: both --from and --to/--version → skip resolve; else default from resolve-target-version.sh (GitVersion).
# Does not edit docs/BREAKING.md — output only (agent pastes + fills body + TOC row).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/repository-link.sh
source "$SCRIPT_DIR/lib/repository-link.sh"
RESOLVE="$SCRIPT_DIR/resolve-target-version.sh"

FROM=""
TO=""
PR=""
OUT=""
BASE="origin/master"

require_value() {
  local flag="$1"
  local value="${2-}"
  if [[ -z "$value" || "$value" == -* ]]; then
    echo "error: $flag requires a non-option value" >&2
    exit 1
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base)
      require_value "$1" "${2-}"
      BASE="$2"
      shift 2
      ;;
    --from)
      require_value "$1" "${2-}"
      FROM="$2"
      shift 2
      ;;
    --to|--version)
      require_value "$1" "${2-}"
      TO="$2"
      shift 2
      ;;
    --pr)
      require_value "$1" "${2-}"
      PR="$2"
      shift 2
      ;;
    --out)
      require_value "$1" "${2-}"
      OUT="$2"
      shift 2
      ;;
    -h|--help)
      sed -n '2,10p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 1
      ;;
  esac
done

read_json() {
  python3 - "$1" "$2" <<'PY'
import json, sys
data = json.loads(sys.argv[2])
print(data.get(sys.argv[1], ""))
PY
}

# Both ends known → scaffold only (no GitVersion / tag resolve).
if [[ -z "$FROM" || -z "$TO" ]]; then
  RESOLVE_ARGS=(--base "$BASE" --json)
  if [[ -n "$TO" ]]; then
    RESOLVE_ARGS+=(--version "$TO")
  fi

  JSON="$("$RESOLVE" "${RESOLVE_ARGS[@]}")" || {
    code=$?
    echo "error: resolve-target-version failed (exit $code) — check GitVersion CLI / GitVersion.yml / tags, or pass --from and --to/--version" >&2
    echo "$JSON" >&2
    exit "$code"
  }

  if [[ -z "$FROM" ]]; then
    FROM="$(read_json breaking_from "$JSON")"
  fi
  if [[ -z "$TO" ]]; then
    TO="$(read_json breaking_to "$JSON")"
  fi
fi

if [[ -z "$FROM" || -z "$TO" ]]; then
  echo "error: could not determine FROM/TO — pass --from and --to/--version" >&2
  exit 1
fi

# Always rebuild from effective FROM/TO (CLI --from/--to may override JSON)
ANCHOR="$(printf 'from-%s-to-%s' "${FROM//./}" "${TO//./}" | tr '[:upper:]' '[:lower:]')"

REPOSITORY_LINK="$(repository_link "$(git remote get-url origin 2>/dev/null || true)")"
PR_SUFFIX=""
if [[ -n "$PR" ]]; then
  PR_SUFFIX=" ([PR #${PR}](${REPOSITORY_LINK}/pull/${PR}))"
fi

BODY="$(cat <<EOF
---

## From ${FROM} to ${TO}

Release: [v${TO}](${REPOSITORY_LINK}/releases/tag/v${TO})${PR_SUFFIX}.

{{BODY}}

EOF
)"

TOC_ROW="| \`${FROM}\` → \`${TO}+\`   | [From ${FROM} to ${TO}](#${ANCHOR})     |"

NOTES="$(cat <<EOF
# BREAKING scaffold (paste manually)

## TOC row (insert after table header in docs/BREAKING.md intro)

${TOC_ROW}

## Section (insert after intro \`---\`, before first existing version block)

${BODY}

Layout rules: .cursor/skills/release-plan/templates/BREAKING-SECTION.md
EOF
)"

if [[ -n "$OUT" ]]; then
  mkdir -p "$(dirname "$OUT")"
  printf '%s\n' "$NOTES" >"$OUT"
  echo "Wrote: $OUT"
else
  printf '%s\n' "$NOTES"
fi
