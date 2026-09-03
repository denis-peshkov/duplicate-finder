#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 <version> <repo-root> <git-token>" >&2
  exit 1
}

VERSION="${1:-}"
REPO_ROOT="${2:-}"
GIT_TOKEN="${3:-}"

if [[ -z "${VERSION}" || -z "${REPO_ROOT}" || -z "${GIT_TOKEN}" ]]; then
  usage
fi

FORMULA_SRC="${REPO_ROOT}/distribution/homebrew-preview/duplicate-finder-preview.rb"
TAP_README_SRC="${REPO_ROOT}/distribution/homebrew-preview/TAP_README.md"
if [[ ! -f "${FORMULA_SRC}" ]]; then
  echo "Formula not found: ${FORMULA_SRC}" >&2
  exit 1
fi

REPO="${GITHUB_REPOSITORY:-denis-peshkov/duplicate-finder}"
BRANCH="homebrew-preview-tap"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "${WORK_DIR}"' EXIT

git clone "https://x-access-token:${GIT_TOKEN}@github.com/${REPO}.git" "${WORK_DIR}/tap"
git -C "${WORK_DIR}/tap" config user.name "Denis Peshkov"
git -C "${WORK_DIR}/tap" config user.email "denis.peshkov@outlook.com"

if git -C "${WORK_DIR}/tap" ls-remote --heads origin "${BRANCH}" | grep -q "${BRANCH}"; then
  git -C "${WORK_DIR}/tap" checkout "${BRANCH}"
else
  git -C "${WORK_DIR}/tap" checkout --orphan "${BRANCH}"
  git -C "${WORK_DIR}/tap" rm -rf . 2>/dev/null || true
fi

mkdir -p "${WORK_DIR}/tap/Formula"
cp "${FORMULA_SRC}" "${WORK_DIR}/tap/Formula/duplicate-finder-preview.rb"
if [[ -f "${TAP_README_SRC}" ]]; then
  cp "${TAP_README_SRC}" "${WORK_DIR}/tap/README.md"
fi

git -C "${WORK_DIR}/tap" add Formula/duplicate-finder-preview.rb README.md 2>/dev/null || git -C "${WORK_DIR}/tap" add Formula/duplicate-finder-preview.rb

if git -C "${WORK_DIR}/tap" diff --cached --quiet; then
  echo "homebrew-preview-tap already has current formula"
  exit 0
fi

git -C "${WORK_DIR}/tap" commit -m "duplicate-finder-preview ${VERSION}"
git -C "${WORK_DIR}/tap" push -u origin "${BRANCH}"

echo "Pushed Formula/duplicate-finder-preview.rb to ${BRANCH}"
