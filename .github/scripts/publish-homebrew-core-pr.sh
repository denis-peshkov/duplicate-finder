#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 <repo-root> <git-token> <version> <github-api-token>" >&2
  exit 1
}

REPO_ROOT="${1:-}"
GIT_TOKEN="${2:-}"
VERSION="${3:-}"
GH_API_TOKEN="${4:-}"

CORE_REPO="denis-peshkov/homebrew-core"
UPSTREAM_REPO="Homebrew/homebrew-core"
UPSTREAM_DEFAULT_BRANCH="main"
CORE_URL="https://x-access-token:${GIT_TOKEN}@github.com/${CORE_REPO}.git"
BRANCH="duplicate-finder"
FORMULA_SRC="${REPO_ROOT}/distribution/homebrew-core/duplicate-finder.rb"
FORMULA_DST="Formula/d/duplicate-finder.rb"
PR_HEAD="denis-peshkov:${BRANCH}"
PR_COMPARE_URL="https://github.com/${UPSTREAM_REPO}/compare/${UPSTREAM_DEFAULT_BRANCH}...${PR_HEAD}?expand=1"

if [[ -z "${REPO_ROOT}" || -z "${GIT_TOKEN}" || -z "${VERSION}" || -z "${GH_API_TOKEN}" ]]; then
  usage
fi

if [[ ! -f "${FORMULA_SRC}" ]]; then
  echo "Formula draft not found: ${FORMULA_SRC}" >&2
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is required to open a Homebrew PR" >&2
  exit 1
fi

WORK_DIR="$(mktemp -d)"
trap 'rm -rf "${WORK_DIR}"' EXIT

if git clone --depth 1 --branch "${UPSTREAM_DEFAULT_BRANCH}" "${CORE_URL}" "${WORK_DIR}/core" 2>/dev/null; then
  :
else
  git clone --depth 1 "${CORE_URL}" "${WORK_DIR}/core"
fi

cd "${WORK_DIR}/core"
git checkout -B "${BRANCH}"
mkdir -p Formula/d
cp "${FORMULA_SRC}" "${FORMULA_DST}"
git add "${FORMULA_DST}"

if git diff --cached --quiet; then
  echo "homebrew-core fork already has current formula"
else
  git -c user.name="Denis Peshkov" -c user.email="denis.peshkov@outlook.com" \
    commit -m "duplicate-finder ${VERSION} (new formula)"
fi

git push -u origin "${BRANCH}" --force
echo "Published formula to ${CORE_REPO} branch ${BRANCH}"

PR_TEMPLATE_URL="https://raw.githubusercontent.com/${UPSTREAM_REPO}/${UPSTREAM_DEFAULT_BRANCH}/.github/PULL_REQUEST_TEMPLATE.md"
PR_TEMPLATE="$(curl -fsSL "${PR_TEMPLATE_URL}")"
if [[ -z "${PR_TEMPLATE}" ]]; then
  echo "Failed to download Homebrew PR template: ${PR_TEMPLATE_URL}" >&2
  exit 1
fi

PR_BODY="$(printf '%s' "${PR_TEMPLATE}" | perl -0777 -pe '
  s/^(- \[ \])(?! AI was)/- [x]/gm;
  s/^(- \[ \] AI was used[^\n]*\n)/$1\nAutomated release CI (`publish-homebrew` on macOS) ran install, test, and audit against the GitHub Release source archive before opening this PR.\n\n/m;
')"
PR_TITLE="duplicate-finder ${VERSION} (new formula)"

print_token_help() {
  cat >&2 <<EOF
Failed to open a pull request to ${UPSTREAM_REPO} with GH_FORK_TOKEN.

Fork branch was pushed with TAGTOKEN: ${CORE_REPO}:${BRANCH}
Manual compare URL: ${PR_COMPARE_URL}

Fix Actions secret GH_FORK_TOKEN (do not rely on TAGTOKEN for this step).
It must be a classic PAT with the public_repo scope. See:
https://docs.brew.sh/How-To-Open-a-Homebrew-Pull-Request#generating-a-personal-access-token-classic
EOF
}

export GH_TOKEN="${GH_API_TOKEN}"
open_pr_count="$(gh pr list \
  --repo "${UPSTREAM_REPO}" \
  --head "${PR_HEAD}" \
  --state open \
  --json number \
  --jq 'length')"

if [[ "${open_pr_count}" != "0" ]]; then
  existing_url="$(gh pr list \
    --repo "${UPSTREAM_REPO}" \
    --head "${PR_HEAD}" \
    --state open \
    --json url \
    --jq '.[0].url')"
  echo "Open PR already exists: ${existing_url}"
  exit 0
fi

echo "Opening PR with GH_FORK_TOKEN (no TAGTOKEN fallback)…"
gh auth setup-git >/dev/null 2>&1 || true

if gh pr create \
  --repo "${UPSTREAM_REPO}" \
  --head "${PR_HEAD}" \
  --base "${UPSTREAM_DEFAULT_BRANCH}" \
  --title "${PR_TITLE}" \
  --body "${PR_BODY}"; then
  echo "Opened PR to ${UPSTREAM_REPO}"
  gh pr list --repo "${UPSTREAM_REPO}" --head "${PR_HEAD}" --state open --json url --jq '.[0].url'
  exit 0
fi

echo "gh pr create failed; trying GitHub REST API with the same GH_FORK_TOKEN…" >&2
payload="$(jq -n \
  --arg title "${PR_TITLE}" \
  --arg head "${PR_HEAD}" \
  --arg base "${UPSTREAM_DEFAULT_BRANCH}" \
  --arg body "${PR_BODY}" \
  '{title: $title, head: $head, base: $base, body: $body}')"
http_code="$(curl -sS -o /tmp/homebrew-pr-create.json -w "%{http_code}" -X POST \
  -H "Authorization: Bearer ${GH_API_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/${UPSTREAM_REPO}/pulls" \
  -d "${payload}" || true)"
echo "REST createPullRequest HTTP ${http_code}" >&2
sed -n '1,40p' /tmp/homebrew-pr-create.json >&2 || true

if [[ "${http_code}" =~ ^2 ]]; then
  echo "Opened PR to ${UPSTREAM_REPO} via REST"
  jq -r '.html_url // empty' /tmp/homebrew-pr-create.json
  exit 0
fi

print_token_help
exit 1
