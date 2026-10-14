#!/usr/bin/env bash
# Collect GitHub issues/PRs metadata for triage (local or CI).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
GH="${ROOT}/.cursor/triage/gh-wrapper.sh"
OUT="${ROOT}/.cursor/triage/docs/.data"
DATE="$(date +%Y-%m-%d)"

mkdir -p "${OUT}"

echo "Collecting triage data into ${OUT} (${DATE})..."

REPO="$("${GH}" repo view --json nameWithOwner -q .nameWithOwner)"
echo "${REPO}" > "${OUT}/repo.txt"

"${GH}" issue list --state open --limit 150 \
  --json number,title,author,createdAt,updatedAt,labels,assignees,body \
  > "${OUT}/issues-open.json"

"${GH}" issue list --state closed --limit 20 \
  --json number,title,labels,closedAt \
  > "${OUT}/issues-closed.json"

"${GH}" pr list --state open --limit 200 \
  --json number,title,author,createdAt,updatedAt,additions,deletions,changedFiles,isDraft,mergeable,reviewDecision,statusCheckRollup,body \
  > "${OUT}/prs-open.json"

if "${GH}" api "repos/${REPO}/collaborators" --jq '.[].login' > "${OUT}/collaborators.txt" 2>/dev/null; then
  :
else
  "${GH}" pr list --state merged --limit 10 --json author --jq '.[].author.login' | sort -u > "${OUT}/collaborators.txt" || true
fi

# PR files for overlap (cap at 30 PRs to limit API calls in CI).
# Emit JSON via gh --jq so paths with quotes/backslash/newlines stay valid JSONL.
PR_NUMS="$("${GH}" pr list --state open --limit 30 --json number -q '.[].number')"
: > "${OUT}/pr-files.jsonl"
for num in ${PR_NUMS}; do
  if ! "${GH}" pr view "${num}" --json files \
    --jq "{number: ${num}, files: [.files[].path]}" \
    >> "${OUT}/pr-files.jsonl" 2>/dev/null; then
    printf '{"number":%s,"files":[]}\n' "${num}" >> "${OUT}/pr-files.jsonl"
  fi
done

echo "Done. Files:"
ls -la "${OUT}"
