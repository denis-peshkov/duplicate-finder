---
name: triage-issue
description: >-
  Issue triage: audit open issues, categorization, duplicates, cross-ref with
  PRs, risk assessment (auth/secrets/licensing), draft comments.
  Args: "all" — deep analysis of all; numbers "42 57" — focus; "ru"/"en" — table
  language (default en).
---

# Issue Triage

GitHub issue triage for the **current repository** (name/layout from `gh repo view` / README).

## When to use

| Scenario | Action |
|---|---|
| "Triage issues" / "issue triage" | Run this skill |
| >10 open issues without triage | Suggest audit |
| Issue stale >30 days | Include in Stale table |

Related skills: `triage-pr`, `triage`, `repo-recap` (if added).

## Prerequisites

```bash
git rev-parse --is-inside-work-tree
gh auth status
```

Use the GitHub CLI wrapper (same entry point in local scripts and CI):

```bash
.cursor/triage/gh-wrapper.sh
```

## Language

- Tables and summary: **English** (default), `ru` — Russian
- GitHub comments: **always English**

## Workflow — 3 phases

### Phase 1 — Audit (always)

#### Data gathering (in parallel)

```bash
REPO=$(.cursor/triage/gh-wrapper.sh repo view --json nameWithOwner -q .nameWithOwner)

.cursor/triage/gh-wrapper.sh issue list --state open --limit 100 \
  --json number,title,author,createdAt,updatedAt,labels,assignees,body,comments

.cursor/triage/gh-wrapper.sh pr list --state open --limit 50 --json number,title,body

.cursor/triage/gh-wrapper.sh issue list --state closed --limit 20 \
  --json number,title,labels,closedAt

.cursor/triage/gh-wrapper.sh api "repos/${REPO}/collaborators" --jq '.[].login'
```

**Collaborators fallback** (403/404):

```bash
.cursor/triage/gh-wrapper.sh pr list --state merged --limit 10 --json author --jq '.[].author.login' | sort -u
```

`author` is an object `{login: "..."}`; extract `.author.login`.

#### Analysis — 6 dimensions

**1. Categorization** (labels > inference from title/body):

- **Bug**: crash, error, fail, broken, regression, token, jwt, auth
- **Feature**: add, implement, support, new, flow, oauth
- **Enhancement**: improve, optimize, refactor, performance
- **Question**: how, why, help, docs, documentation
- **Duplicate Candidate**: see item 3

**2. Cross-ref PRs**:

- Scan PR body: `fixes #N`, `closes #N`, `resolves #N`
- Map: `issue_number → [PR numbers]`
- PR merged + issue open → recommend closing

**3. Duplicates**:

- Jaccard on title words >60% → candidate
- Overlap keywords in body >50% → stronger signal
- Compare with 20 most recent closed

**4. Risk** (security priority):

- **Red**: CVE, vulnerability, injection, auth bypass, security, exploit, token leak, credentials, RCE, XSS, jwt bypass, refresh token
- **Yellow**: breaking change, migration, deprecation, API removal, incompatible
- **Green**: everything else

**5. Staleness**:

- >30d without activity → Stale
- >90d → Very Stale

**6. Recommendations**:

- `Accept & Prioritize`, `Label needed`, `Comment needed`, `Linked to PR`,
  `Duplicate candidate`, `Close candidate` (not for collaborator), `PR merged → close`

#### Output — 5 tables

See format in the original workflow (Critiques / Linked to PR / Active / Duplicates / Stale + Summary).

0 issues → `No open issues.` and finish.

After tables — copy to clipboard (`pbcopy` / `xclip` / `wl-copy`).

### Phase 2 — Deep Analysis (opt-in)

For selected issues — `Task` with `subagent_type: generalPurpose` in parallel.

Repository context for the agent (from README / tree, not hard-coded paths):

- Library / `src/` — public API, DI, pipeline
- `*Tests*/` — automated tests
- Documentation: `README.md`, `docs/BREAKING.md`, `docs/CHANGELOG.md` (when present)
- Rules: `.cursor/triage/post-pr-triage.mjs` (`loadMatchedRules` → `.cursor/rules/*.mdc` by `alwaysApply` / `globs`)

Comment template: `templates/issue-comment.md`.

### Phase 3 — Actions (confirmation only)

- `.cursor/triage/gh-wrapper.sh issue comment {num} --body-file -`
- `.cursor/triage/gh-wrapper.sh issue edit {num} --add-label "{label}"`
- `.cursor/triage/gh-wrapper.sh issue close {num} --reason "not planned"`

**Never** post/close without `AskQuestion`.

## Comment specifics

For bug reports request:

- Package / NuGet version or git commit
- Target framework (e.g. net8.0)
- Area (from README / folder layout)
- Reproduction steps without real secrets/tokens/license keys

## Edge cases

| Situation | Behavior |
|---|---|
| 0 issues | Report and exit |
| >50 comments | Summarize 5 most recent |
| Rate limit | Reduce `--limit`, notify |
| Issue collaborator | Do not suggest close without explicit request |

## Saving the report

On full triage save to `.cursor/triage/docs/issues-YYYY-MM-DD.md`.
