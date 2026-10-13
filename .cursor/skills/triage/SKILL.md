---
name: triage
description: >-
  Full triage orchestrator: GitHub issues×PRs cross-analysis, OR local/branch
  review vs master|dev (no PR). Args: "local", "branch <name>", "base master|dev",
  "offline", "ru"/"en" (default en), "no save" — skip file; "deep" — Phase 2 review
  on local/branch. Default without local/branch args = GitHub open issues + PRs.
---

# Triage (orchestrator)

Two modes:

| Mode | Trigger | What runs |
|---|---|---|
| **GitHub** (default) | `triage` / `запусти triage` without `local`/`branch` | `triage-issue` + `triage-pr` Phase 1 + cross-analysis issues×PRs |
| **Local / branch** | `local` · `branch <name>` · «текущая ветка» · «vs master» without PR | `triage-pr` **Phase 1b** (`git diff` vs base) — **not** GitHub PR list |

Cross-ref skills: [`triage-issue`](../triage-issue/SKILL.md), [`triage-pr`](../triage-pr/SKILL.md) (Phase 1b + optional Phase 2).

## When to use

- Weekly or before NuGet release → **GitHub** mode
- Before sprint planning → **GitHub** mode
- After CI `triage.yml` → interpret artifacts (**GitHub**)
- Review **current branch vs master** before opening a PR → **Local** mode
- Named branch not checked out → **Branch** mode

## Args

| Arg | Effect |
|---|---|
| _(none)_ | GitHub mode |
| `local` | Current `HEAD` vs base (default `origin/master`) |
| `branch <name>` | Named ref vs base (resolves local or `origin/<name>`) |
| `base master\|dev` | Diff base (default **master**) |
| `offline` | Skip `git fetch` (stale base warning) — Phase 1b only |
| `deep` | After Phase 1b, run `triage-pr` Phase 2 (deep review) |
| `ru` / `en` | Table language (default **en**) |
| `no save` | Skip writing report file |

Examples (chat):

- `запусти triage` → GitHub
- `запусти triage local` / `triage local ru` → текущая ветка vs `origin/master`
- `triage local base dev` → vs `origin/dev`
- `triage branch release/fix-missed-issues ru`
- `triage local deep` → summary + deep review

If the user says «локально», «текущая ветка», «без PR», «vs master» and does **not** ask for open PRs/issues — choose **Local** mode even without the literal word `local`.

## Mode: Local / branch (no PR)

**Do not** require `gh` or `collect-data.sh`. **Do not** post GitHub comments.

### Phase L1 — Prerequisites

```bash
git rev-parse --is-inside-work-tree
date +%Y-%m-%d
git branch --show-current
```

### Phase L2 — Diff (follow `triage-pr` Phase 1b)

Resolve `BASE_REF` / `BRANCH_REF` per [`triage-pr` Phase 1b](../triage-pr/SKILL.md) (`offline` rules, remote-only branch → `origin/$BRANCH`).

```bash
git log --oneline "$BASE_REF..$BRANCH_REF" | head -40
git diff --stat "$BASE_REF...$BRANCH_REF"
git diff --name-status "$BASE_REF...$BRANCH_REF"
# Prefer reading hotspots; full diff if needed for deep.
# Replace 'path/' / 'tests-path/' with real prefixes from --name-status above.
git diff "$BASE_REF...$BRANCH_REF" -- 'path/' 'tests-path/'
```

Size bands + hotspots: same as `triage-pr` Phase 1. CI / mergeable / reviews → **N/A (branch mode)**.

### Phase L3 — Optional deep (`deep` or user asks)

`triage-pr` Phase 2 via `.cursor/rules/*.mdc` (`post-pr-triage.mjs` → `loadMatchedRules`). Optional `Task` bugbot.

### Phase L4 — Output + save

Chat: short summary (commits, size, hotspots, risks, priority actions) + offer deep if not run.

Save (unless `no save`):

- `.cursor/triage/docs/branch-<safe-name>-YYYY-MM-DD.md`
  (`/` → `-` in branch name; for `local` use current branch name)

Suggested file structure:

```markdown
# Branch triage — <branch> vs <base> — YYYY-MM-DD

## Summary
## Commits
## Diff stat / hotspots
## Risks (auth/JWT if any)
## Priority actions
## Numeric summary (files, +/- lines, commits)
```

If a matching open PR exists for this head, **mention** its URL in the report (optional `gh`); still triage the **git delta**, not only PR metadata.

---

## Mode: GitHub (default)

### Phase 1 — Prerequisites

```bash
git rev-parse --is-inside-work-tree
.cursor/triage/gh-wrapper.sh auth status
date +%Y-%m-%d
```

Or:

```bash
.cursor/triage/collect-data.sh
```

**Auto-hint:** after GitHub Phase 1, if open PRs = 0 **and** current branch is ahead of `origin/master` (or `origin/dev`) — add a short note: «локальная ветка без PR — можно `triage local`» and optionally run Phase L2 in the **same** report under «Local branch (no PR)» if the user is clearly on a release/feature branch. Prefer asking only when ambiguous; if user said plain «запусти triage» on `release/*` / `hotfix/*` with 0 PRs for this head, **include** local branch section automatically.

### Phase 2 — Data gathering (in parallel)

**Issues** (via `gh-wrapper.sh`):

```bash
.cursor/triage/gh-wrapper.sh issue list --state open --limit 150 \
  --json number,title,author,createdAt,updatedAt,labels,assignees,body

.cursor/triage/gh-wrapper.sh issue list --state closed --limit 20 \
  --json number,title,labels,closedAt
```

**PRs**:

```bash
.cursor/triage/gh-wrapper.sh pr list --state open --limit 200 \
  --json number,title,author,createdAt,updatedAt,additions,deletions,changedFiles,isDraft,mergeable,reviewDecision,statusCheckRollup,body
```

PR files — for overlap detection (see `triage-pr`).

### Phase 3 — Individual triage

`triage-issue` + `triage-pr` Phase 1 (open PR tables). CI classification: **External — ready** only when CI clean (`SUCCESS`); unstable/unknown → problematic (see `triage-pr`).

### Phase 4 — Cross-analysis

#### 4.1 Double coverage — 2 PRs for 1 issue

| Issue | PR1 | PR2 | Verdict |
|---|---|---|---|

Rules: smaller scope, CI clean, internal PR, overlap >80% → conflict.

#### 4.2 Security gaps

For issues with "red" risk — findings without PR (especially license JWT, secret leaks).

#### 4.3 P0/P1 without PR

Labels/keywords: crash, auth, token, jwt, security.

#### 4.4 Our PRs dirty

CI dirty / CONFLICTING — reason (overlap, rebase needed). Unstable ≠ dirty; list under unstable.

#### 4.5 PR without `fixes #N`

Internal PRs not linked to an issue.

### Phase 5 — Output

Summary:

| Category | Count |
|---|---|
| PRs ready to merge (ours) | N |
| Quick wins (external) | N |
| Double coverage | N |
| P0/P1 without PR | N |
| Security without PR | N |
| Dirty PRs | N |
| Local branch without PR (if included) | 0/1 |

### Saving

`.cursor/triage/docs/triage-YYYY-MM-DD.md` (unless `no save`).

```markdown
# Triage — YYYY-MM-DD

## Issues (tables)
## PRs (tables)
## Local branch (optional)
## 1. Double coverage
## 2. Security gaps
## 3. P0/P1 without PR
## 4. Dirty PRs
## 5. Priority actions
## Numeric summary
```

## CI integration

After `triage.yml` read:

- `.cursor/triage/docs/.data/*.json` — raw data
- `.cursor/triage/docs/ci-report-YYYY-MM-DD.md` — CI agent report

Supplement with cross-analysis manually if needed.

## Rules

- GitHub actions (comments/close) — only with `AskQuestion`
- Table language: en (default), ru via argument
- GitHub `gh` commands — always `.cursor/triage/gh-wrapper.sh`
- Local/branch mode — git only (unless mentioning an existing PR URL)
