---
name: triage-pr
description: >-
  PR triage: audit open PRs, deep review, draft review comments; local/branch
  review vs master|dev without a PR. Args: "all", PR numbers, "branch <name>",
  "local", "base master|dev", "offline", "ru"/"en" for table language (default en).
---

# PR Triage

## When to use

| Scenario | Action |
|---|---|
| "Triage PRs" / "pr triage" | Phase 1 audit (GitHub open PRs) |
| "Triage this branch" / "local triage" / "triage local" | Phase 1b (git diff vs master\|dev, no PR) |
| "Review branch X vs master" | Phase 1b + Phase 2 |
| Orchestrator `triage local` / `triage branch …` | Same as Phase 1b (see `triage` skill) |
| >5 open PRs without review | Suggest Phase 1 audit |
| PR stale >14 days | Flag in table |

## Modes

| Mode | Args / trigger | Diff source | GitHub comment |
|---|---|---|---|
| **PR audit** | `all` or default | `gh pr list` | No (draft only) |
| **PR deep** | PR number(s) | `gh pr diff {n}` | AskQuestion + template |
| **Branch** | `branch <name>` `[base master\|dev]` `[offline]` | `git diff base...branch` | No |
| **Local** | `local` `[base master\|dev]` `[offline]` | `git diff base...HEAD` (+ uncommitted if asked) | No |

Default **base**: `master` if ambiguous; use `dev` when the user says so or the branch targets `dev`.

Prefer `origin/<base>` after a **successful** `git fetch`. Do **not** swallow fetch failures unless the user passed **`offline`** (see Phase 1b).

## Prerequisites

```bash
git rev-parse --is-inside-work-tree
```

For **PR** modes only:

```bash
gh auth status
```

GitHub commands — via `.cursor/triage/gh-wrapper.sh`.

## Language

- Tables: English (default), `ru` — Russian
- GitHub comments: English
- Branch/local report: same as tables language

## Phase 1 — Audit (open PRs)

### Data gathering

```bash
REPO=$(.cursor/triage/gh-wrapper.sh repo view --json nameWithOwner -q .nameWithOwner)

.cursor/triage/gh-wrapper.sh pr list --state open --limit 50 \
  --json number,title,author,createdAt,updatedAt,additions,deletions,changedFiles,isDraft,mergeable,reviewDecision,statusCheckRollup,body

.cursor/triage/gh-wrapper.sh api "repos/${REPO}/collaborators" --jq '.[].login'
```

For each PR (priority — overlap candidates):

```bash
.cursor/triage/gh-wrapper.sh api "repos/${REPO}/pulls/{num}/reviews" \
  --jq '[.[] | .user.login + ":" + .state] | join(", ")'

.cursor/triage/gh-wrapper.sh pr view {num} --json files --jq '[.files[].path] | join(",")'
```

### Classification

**Size**: XS <50, S 50–200, M 200–500, L 500–1000, XL >1000 additions.

**Detections**: overlaps >50% files, clusters (3+ PRs from same author), stale >14d, CI clean/unstable/dirty.

**Our PRs**: author in collaborators.

**CI rollup** (`statusCheckRollup.state` from `gh pr list`): `SUCCESS` → clean; `FAILURE` → dirty; `PENDING` / missing / anything else → unstable or unknown.

**External — ready**: ≤1000 additions, ≤10 files, not CONFLICTING, **CI clean only** (`SUCCESS` — all required checks passed).

**External — problematic**: XL, conflict, **CI unstable/dirty/unknown**, overlap.

### Output tables

Sections: Our PRs / External ready / External problematic + Summary.

0 PRs → finish (or offer Phase 1b if user is on a feature/hotfix branch).

### File hotspots

Prefer paths from the PR / branch delta (`git diff --name-status`) and README layout. Examples of areas to prioritize when present:

- library / `src/` — public API, DI registration, pipeline
- `*Tests*/` — coverage for new behavior
- sample / host app — smoke usage only
- `.github/workflows/`, `docs/` — CI and consumer docs

## Phase 1b — Branch / local (no PR)

Use when the user asks for local branch, named branch, or review without a PR. **Do not** require `gh` or post GitHub comments.

### Resolve refs

Default: refresh remote base; **fail** if fetch cannot run. **`offline`** (user arg): skip fetch; allow local base with an explicit warning in the report.

```bash
BASE="${BASE:-master}"          # or: dev
BRANCH="${BRANCH:-HEAD}"        # local: HEAD; named: hotfix/foo (origin/hotfix/foo → stripped to hotfix/foo)
OFFLINE=0                       # 1 when user passed "offline"

if [[ "$OFFLINE" -eq 0 ]]; then
  if ! git fetch origin "$BASE"; then
    echo "error: git fetch origin $BASE failed — fix network/auth or retry with offline" >&2
    exit 1
  fi
  if ! git rev-parse --verify "origin/$BASE" >/dev/null 2>&1; then
    echo "error: origin/$BASE missing after fetch" >&2
    exit 1
  fi
  BASE_REF="origin/$BASE"
else
  if git rev-parse --verify "origin/$BASE" >/dev/null 2>&1; then
    BASE_REF="origin/$BASE"
  elif git rev-parse --verify "$BASE" >/dev/null 2>&1; then
    BASE_REF="$BASE"
    # Report must note: offline mode — base may be stale
  else
    echo "error: neither origin/$BASE nor local $BASE exists" >&2
    exit 1
  fi
fi

# Resolve branch tip (local mode: HEAD; named: foo or origin/foo)
if [[ "$BRANCH" == "HEAD" ]]; then
  BRANCH_REF="HEAD"
else
  # Strip leading origin/ so fetch/ref never become origin/origin/…
  BRANCH="${BRANCH#origin/}"
  if git rev-parse --verify "$BRANCH" >/dev/null 2>&1; then
    BRANCH_REF="$BRANCH"
  else
    if [[ "$OFFLINE" -eq 0 ]]; then
      git fetch origin "$BRANCH" 2>/dev/null || true
    fi
    if git rev-parse --verify "origin/$BRANCH" >/dev/null 2>&1; then
      BRANCH_REF="origin/$BRANCH"
    else
      echo "error: branch '$BRANCH' not found (local or origin/)" >&2
      exit 1
    fi
  fi
fi
```

Use **`$BRANCH_REF`** (not `$BRANCH`) in all log/diff commands below.

### Collect diff

```bash
git log --oneline "$BASE_REF..$BRANCH_REF" | head -30
git diff --stat "$BASE_REF...$BRANCH_REF"
git diff --name-status "$BASE_REF...$BRANCH_REF"
git diff "$BASE_REF...$BRANCH_REF"
```

Triple-dot (`...`) = changes on the branch since fork from base (merge-base). Prefer this over two-dot for triage.

**Uncommitted** (only if user asks `local` + working tree / uncommitted):

```bash
git status -sb
git diff --stat
git diff --cached --stat
git diff
git diff --cached
```

### Size / hotspots

Same size bands and file hotspots as Phase 1. No CI / mergeable / reviews — note "N/A (branch mode)".

### Output

Short summary + file list + offer Phase 2 deep review. Save under Saving below.

## Phase 2 — Deep Review (opt-in)

`Task` with `subagent_type: bugbot` or `generalPurpose` in parallel.

**PR mode:**

```bash
.cursor/triage/gh-wrapper.sh pr diff {num}
```

**Branch / local mode:**

```bash
git diff "$BASE_REF...$BRANCH_REF"
# or uncommitted: git diff && git diff --cached
```

Repository context for the agent (from README / tree, not hard-coded paths):

- Library / `src/` — public API, DI, pipeline
- `*Tests*/` — automated tests
- Documentation: `README.md`, `docs/BREAKING.md`, `docs/CHANGELOG.md` (when present)
- Rules: `.cursor/triage/post-pr-triage.mjs` (`loadMatchedRules` → `.cursor/rules/*.mdc` by `alwaysApply` / `globs`)

Response structure: Critical 🔴 / Important 🟠 / Suggestions 🟡 / What's Good ✅.

## Phase 3 — Comments (AskQuestion required)

Template: `templates/review-comment.md` (manual deep review). **PR mode only.**

Branch/local: report in chat and/or save file — **never** `gh pr comment` unless the user points at an existing PR number.

### Automated PR comment (CI)

On `pull_request` opened/synchronize CI posts an automated triage comment (category, priority, confidence, summary, files):

- Script: `.cursor/triage/post-pr-triage.mjs`
- Template: `.cursor/triage/templates/pr-automated-triage-comment.md`
- Marker: `<!-- triage -->` (update on push, no duplication)
- Draft PR — skip

For a **single-PR automated comment** (same as CI), prefer:

```bash
PR_NUMBER=42 CURSOR_API_KEY=... yarn pr-triage
```

(from `.cursor/triage/`), not a parallel template.

```bash
.cursor/triage/gh-wrapper.sh pr comment {num} --body-file -
```

## Saving

- PR audit: `.cursor/triage/docs/prs-YYYY-MM-DD.md`
- Branch/local: `.cursor/triage/docs/branch-<safe-name>-YYYY-MM-DD.md`  
  (sanitize branch name: `/` → `-`)
