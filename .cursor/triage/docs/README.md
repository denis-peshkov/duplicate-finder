# Automated Triage Reports

Triage reports for the **current repository** (name and URL — from `gh repo view` / git remote).

## Locally (Cursor Agent + skills)

```text
# GitHub: open issues + PRs + cross-analysis
Run triage
запусти triage

# Local: current branch vs origin/master (no PR required)
triage local
запусти triage local
triage local ru
triage local deep

# Named branch
triage branch release/fix-missed-issues base master

# Parts
Run triage-issue
Run triage-pr
triage-pr local
```

Skills: `.cursor/skills/{triage-issue,triage-pr,triage}/`

Reports:

- GitHub → `.cursor/triage/docs/triage-YYYY-MM-DD.md`
- Local/branch → `.cursor/triage/docs/branch-<safe-name>-YYYY-MM-DD.md`


## Scripts

```bash
# Data collection
bash .cursor/triage/collect-data.sh

# CI agent (requires CURSOR_API_KEY, Node 20.19.4)
cd .cursor/triage && yarn install --ignore-engines && CURSOR_API_KEY=... yarn triage
```

On Node 20 the SDK uses `JsonlLocalAgentStore` (`cursor-agent-local.mjs`), not `node:sqlite`.

## CI

Workflow `.github/workflows/triage.yml`:

- **Schedule**: Monday 06:00 UTC
- **workflow_dispatch**: manual run
- **issues opened**: data collection
- **pull_request** opened/synchronize/reopened: AI comment on the PR (category, priority, confidence; same-repo, non-draft; needs `CURSOR_API_KEY`)

### Secrets

| Secret | Required | Purpose |
|---|---|---|
| `CURSOR_API_KEY` | Yes (for the AI report) | Cursor SDK in CI |
| `GITHUB_TOKEN` | Auto | `gh` CLI |

Create a key: [Cursor Dashboard → Integrations](https://cursor.com/dashboard/integrations)

### PR opened / updated

Workflow `triage.yml` → job **PR automated comment**:

- Cursor Agent analyzes the **full PR** (`base...head`: **all** commits + files). Diff is `gh pr diff` / API patches for the whole PR — **not** tip-commit-only / last synchronize patch
- Prompt always lists every commit in the PR; category/priority/labels must reflect the cumulative delta
- Checkout uses `fetch-depth: 0` so local agent tools are not limited to a shallow tip
- Posts an automated triage comment (category, priority, confidence, summary, files)
- Review guidance: matched `.cursor/rules/*.mdc` via `alwaysApply` / `globs` (`load-review-rules.mjs`) — see [`.cursor/README.md`](../../README.md)
- Syncs GitHub labels `{category}` / `priority:{priority}` by default when confidence ≥ `TRIAGE_LABEL_MIN_CONFIDENCE` (default `70`); set `TRIAGE_APPLY_LABELS=false` to disable. Allowlisted values only
- On a new push **updates** the same comment (marker `<!-- triage -->` + author `github-actions[bot]`) and re-evaluates labels on the **same full** base...head scope

Manual test: **Actions → Triage → Run workflow** → `pr_number` field.

Optional env (CI / local):

| Env | Purpose |
|---|---|
| `TRIAGE_APPLY_LABELS` | Sync GitHub labels from agent JSON (default: `1` / on; `false` / `0` / `no` / `off` to disable) |
| `TRIAGE_LABEL_MIN_CONFIDENCE` | Min agent confidence (0–100) required when labels are enabled (default `70`) |
| `TRIAGE_ICON_REL_PATH` | Repo-relative icon for PR comment header (e.g. `icon.png`) |
| `TRIAGE_ICON_BRANCH` | Branch for raw.githubusercontent icon URL (default `master`) |
| `TRIAGE_PATCH_PRIORITY_PREFIXES` | Comma-separated top-level dirs to prefer in truncated diffs (else inferred from PR files) |

### Artifacts

- `.cursor/triage/docs/ci-report-YYYY-MM-DD.md`
- `.cursor/triage/docs/.data/*.json` (in the artifact, not in git)

### GitHub CLI

Triage scripts call `.cursor/triage/gh-wrapper.sh`, which delegates to `gh` (preinstalled on GitHub Actions runners; locally via `gh auth login`).
