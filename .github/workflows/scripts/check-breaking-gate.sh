#!/usr/bin/env bash
# Gate consumer-breaking PRs: label breaking-changes, require owner-applied breaking-approved.
# Usage: check-breaking-gate.sh
# Required env: GH_TOKEN, GITHUB_REPOSITORY, PR_NUMBER, PR_TITLE, BASE_SHA, HEAD_SHA, REPO_OWNER
set -euo pipefail

: "${GH_TOKEN:?}"
: "${GITHUB_REPOSITORY:?}"
: "${PR_NUMBER:?}"
: "${PR_TITLE:?}"
: "${BASE_SHA:?}"
: "${HEAD_SHA:?}"
: "${REPO_OWNER:?}"

LABEL_CHANGES="breaking-changes"
LABEL_APPROVED="breaking-approved"
BREAKING_DOC="docs/BREAKING.md"
COMMENT_MARKER="<!-- breaking-gate-lookup-marker -->"

ensure_label() {
  local name="$1"
  local color="$2"
  local desc="$3"
  gh label create "$name" --color "$color" --description "$desc" --force >/dev/null 2>&1 || true
}

has_label() {
  local name="$1"
  gh pr view "$PR_NUMBER" --repo "$GITHUB_REPOSITORY" --json labels --jq '.labels[].name' \
    | grep -Fxq "$name"
}

add_label() {
  local name="$1"
  if has_label "$name"; then
    return 0
  fi
  gh pr edit "$PR_NUMBER" --repo "$GITHUB_REPOSITORY" --add-label "$name"
}

remove_label() {
  local name="$1"
  if ! has_label "$name"; then
    return 0
  fi
  gh pr edit "$PR_NUMBER" --repo "$GITHUB_REPOSITORY" --remove-label "$name"
}

# Latest actor who applied LABEL_APPROVED (empty if never / unknown).
approved_label_actor() {
  # Paginate raw events, then take the last matching actor (jq per page would be wrong).
  gh api --paginate \
    -H "Accept: application/vnd.github+json" \
    "repos/${GITHUB_REPOSITORY}/issues/${PR_NUMBER}/timeline" \
    --jq '.[] | select(.event == "labeled" and .label.name == "breaking-approved") | .actor.login' \
    | tail -n1
}

upsert_breaking_comment() {
  local body
  body=$(cat <<EOF
${COMMENT_MARKER}
## Breaking change gate

This PR looks consumer-breaking (\`BREAKING:\` title and/or changes to \`${BREAKING_DOC}\`).

- CI added the \`${LABEL_CHANGES}\` label.
- Merge stays blocked until the **repository owner** (\`${REPO_OWNER}\`) adds \`${LABEL_APPROVED}\`.
- A comment containing \`${LABEL_APPROVED}\` is **not** enough — only that label from the owner unblocks the check.
EOF
)

  local comment_id
  comment_id=$(gh api "repos/${GITHUB_REPOSITORY}/issues/${PR_NUMBER}/comments" \
    --jq ".[] | select(.body | contains(\"${COMMENT_MARKER}\")) | .id" | head -n1)

  if [ -n "${comment_id:-}" ]; then
    gh api "repos/${GITHUB_REPOSITORY}/issues/comments/${comment_id}" \
      -X PATCH \
      -f body="$body" >/dev/null
  else
    gh pr comment "$PR_NUMBER" --repo "$GITHUB_REPOSITORY" --body "$body" >/dev/null
  fi
}

title_is_breaking=0
if printf '%s' "$PR_TITLE" | grep -qiE '^BREAKING:'; then
  title_is_breaking=1
fi

# Ensure both ends of the PR diff are present (forks / shallow edge cases).
git fetch --no-tags --depth=1 origin "$BASE_SHA" "$HEAD_SHA" >/dev/null 2>&1 || true

doc_changed=0
if git diff --name-only "${BASE_SHA}...${HEAD_SHA}" -- "$BREAKING_DOC" | grep -qx "$BREAKING_DOC"; then
  doc_changed=1
fi

is_breaking=0
if [ "$title_is_breaking" = "1" ] || [ "$doc_changed" = "1" ]; then
  is_breaking=1
fi

echo "PR #${PR_NUMBER}: title_breaking=${title_is_breaking} ${BREAKING_DOC}_changed=${doc_changed}"

ensure_label "$LABEL_CHANGES" "b60205" "Consumer-breaking signals detected (BREAKING: title and/or docs/BREAKING.md)"
ensure_label "$LABEL_APPROVED" "0e8a16" "Owner approved consumer-breaking change (unblocks breaking-gate)"

if [ "$is_breaking" != "1" ]; then
  remove_label "$LABEL_CHANGES"
  echo "No consumer-breaking signals — gate passed."
  exit 0
fi

add_label "$LABEL_CHANGES"
upsert_breaking_comment

if ! has_label "$LABEL_APPROVED"; then
  echo "::error::Breaking changes detected but '${LABEL_APPROVED}' is missing. Repository owner (${REPO_OWNER}) must add that label to unblock."
  exit 1
fi

actor="$(approved_label_actor || true)"
if [ -z "${actor:-}" ]; then
  echo "::error::Label '${LABEL_APPROVED}' is present but timeline has no labeled event for it; cannot verify the actor."
  exit 1
fi

if [ "$actor" != "$REPO_OWNER" ]; then
  echo "::error::Label '${LABEL_APPROVED}' was applied by '${actor}', but only repository owner (${REPO_OWNER}) may approve breaking changes."
  exit 1
fi

echo "Breaking changes approved by repository owner (${actor}) — gate passed."
exit 0
