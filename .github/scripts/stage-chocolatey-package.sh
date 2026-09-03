#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 <version> <windows-zip> <repo-root> <output-dir>" >&2
  echo "Preview: set CHANNEL=preview plus COMMIT_SHA, BRANCH, and CI_RUN_URL." >&2
  exit 1
}

VERSION="${1:-}"
WINDOWS_ZIP="${2:-}"
REPO_ROOT="${3:-}"
OUTPUT_DIR="${4:-}"
CHANNEL="${CHANNEL:-release}"
COMMIT_SHA="${COMMIT_SHA:-}"
BRANCH="${BRANCH:-}"
CI_RUN_URL="${CI_RUN_URL:-}"
GITHUB_REPO="${GITHUB_REPOSITORY:-denis-peshkov/duplicate-finder}"

if [[ -z "${VERSION}" || -z "${WINDOWS_ZIP}" || -z "${REPO_ROOT}" || -z "${OUTPUT_DIR}" ]]; then
  usage
fi

if [[ ! -f "${WINDOWS_ZIP}" ]]; then
  echo "Windows release archive not found: ${WINDOWS_ZIP}" >&2
  exit 1
fi

TEMPLATE_DIR="${REPO_ROOT}/distribution/chocolatey/duplicate-finder"
NUSPEC_TEMPLATE="${TEMPLATE_DIR}/duplicate-finder.nuspec"
LICENSE_SRC="${REPO_ROOT}/LICENSE"

if [[ ! -f "${NUSPEC_TEMPLATE}" ]]; then
  echo "Chocolatey template not found: ${NUSPEC_TEMPLATE}" >&2
  exit 1
fi

if [[ ! -f "${LICENSE_SRC}" ]]; then
  echo "LICENSE not found: ${LICENSE_SRC}" >&2
  exit 1
fi

if [[ "${CHANNEL}" == "preview" ]]; then
  VERIFICATION_TEMPLATE="${TEMPLATE_DIR}/tools/VERIFICATION-preview.txt"
  if [[ -z "${COMMIT_SHA}" || -z "${BRANCH}" || -z "${CI_RUN_URL}" ]]; then
    echo "Preview packaging requires COMMIT_SHA, BRANCH, and CI_RUN_URL." >&2
    exit 1
  fi
else
  VERIFICATION_TEMPLATE="${TEMPLATE_DIR}/tools/VERIFICATION.txt"
fi

if [[ ! -f "${VERIFICATION_TEMPLATE}" ]]; then
  echo "VERIFICATION template not found: ${VERIFICATION_TEMPLATE}" >&2
  exit 1
fi

STAGING="${OUTPUT_DIR}/staging"
rm -rf "${STAGING}"
mkdir -p "${STAGING}/tools" "${OUTPUT_DIR}"

cp "${NUSPEC_TEMPLATE}" "${STAGING}/duplicate-finder.nuspec"
cp "${TEMPLATE_DIR}/tools/"*.ps1 "${STAGING}/tools/"
cp "${LICENSE_SRC}" "${STAGING}/tools/LICENSE.txt"

unzip -j -o "${WINDOWS_ZIP}" "DuplicateFinder.exe" -d "${STAGING}/tools/"

if [[ ! -f "${STAGING}/tools/DuplicateFinder.exe" ]]; then
  echo "DuplicateFinder.exe not found in ${WINDOWS_ZIP}" >&2
  exit 1
fi

if command -v sha256sum >/dev/null 2>&1; then
  EXE_SHA256="$(sha256sum "${STAGING}/tools/DuplicateFinder.exe" | awk '{print toupper($1)}')"
else
  EXE_SHA256="$(shasum -a 256 "${STAGING}/tools/DuplicateFinder.exe" | awk '{print toupper($1)}')"
fi

if [[ "${CHANNEL}" == "preview" ]]; then
  SOURCE_ARCHIVE_URL="https://github.com/${GITHUB_REPO}/archive/${COMMIT_SHA}.tar.gz"
  perl -pe \
    "s|__COMMIT_SHA__|${COMMIT_SHA}|g; s|__BRANCH__|${BRANCH}|g; s|__CI_RUN_URL__|${CI_RUN_URL}|g; s|__SOURCE_ARCHIVE_URL__|${SOURCE_ARCHIVE_URL}|g; s|__EXE_SHA256__|${EXE_SHA256}|g" \
    "${VERIFICATION_TEMPLATE}" > "${STAGING}/tools/VERIFICATION.txt"
else
  RELEASE_URL="https://github.com/${GITHUB_REPO}/releases/download/v${VERSION}/duplicate-finder-${VERSION}-x86_64-pc-windows-msvc.zip"
  perl -pe "s|__RELEASE_URL__|${RELEASE_URL}|g; s|__EXE_SHA256__|${EXE_SHA256}|g" \
    "${VERIFICATION_TEMPLATE}" > "${STAGING}/tools/VERIFICATION.txt"
fi

perl -pi -e "s|<version>.*</version>|<version>${VERSION}</version>|" "${STAGING}/duplicate-finder.nuspec"

if ! command -v choco >/dev/null 2>&1; then
  echo "Chocolatey CLI (choco) is required to pack packages with Chocolatey nuspec metadata." >&2
  echo "Run on windows-latest in CI, or install choco locally." >&2
  exit 1
fi

choco pack "${STAGING}/duplicate-finder.nuspec" \
  --version="${VERSION}" \
  --outputdirectory="${OUTPUT_DIR}"

echo "Packed Chocolatey package: ${OUTPUT_DIR}/duplicate-finder.${VERSION}.nupkg"
