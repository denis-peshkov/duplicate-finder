#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 <version> <repo-root> <output-dir>" >&2
  exit 1
}

VERSION="${1:-}"
REPO_ROOT="${2:-}"
OUT_DIR="${3:-}"

if [[ -z "${VERSION}" || -z "${REPO_ROOT}" || -z "${OUT_DIR}" ]]; then
  usage
fi

if [[ ! -d "${REPO_ROOT}" ]]; then
  echo "Repository root not found: ${REPO_ROOT}" >&2
  exit 1
fi

ARCHIVE="${OUT_DIR}/duplicate-finder-${VERSION}-src.tar.gz"
mkdir -p "${OUT_DIR}"
rm -f "${ARCHIVE}"

WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

git -C "${REPO_ROOT}" archive --format=tar --prefix=duplicate-finder/ HEAD \
  | tar -x -C "${WORK}"

perl -pi -e "s/^version = \".*\"/version = \"${VERSION}\"/" "${WORK}/duplicate-finder/pyproject.toml"
perl -pi -e "s/^APP_VERSION = \".*\"/APP_VERSION = \"${VERSION}\"/" "${WORK}/duplicate-finder/src/config/app_info.py"

tar -czf "${ARCHIVE}" -C "${WORK}" duplicate-finder
echo "${ARCHIVE}"
