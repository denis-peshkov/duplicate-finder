# Duplicate Finder — GitHub Ruleset recipes

Importable JSON for [repository rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository), aligned with `CONTRIBUTING.md` branch policy.

Based on [github/ruleset-recipes](https://github.com/github/ruleset-recipes).

## Prerequisite

`duplicate-finder` is a **public** repository, so repository rulesets are available without GitHub Pro.

Until rulesets are imported and set to **Active**, keep enforcing policy via `.github/workflows/branch-policy.yml`.

## Import

1. Open the repo → **Settings** → **Rules** → **Rulesets**.
2. **New ruleset** → **Import a ruleset**.
3. Import files below **one by one** (order recommended).
4. Review each ruleset:
   - Confirm **status check** context is `Test` (job name in `.github/workflows/ci.yml`). If GitHub shows a different name (e.g. `CI / Test`), edit the required check after the first green run.
   - Confirm **Bypass** is Repository admin only (`RepositoryRole` / Admin).
5. Save with **Active** (or start with **Evaluate** if available on your plan).

## Files

| File | Target | Purpose |
|---|---|---|
| [`01-protect-master.json`](01-protect-master.json) | `master` | No force-push/delete; PR + CI required; admin bypass for releases |
| [`02-protect-dev.json`](02-protect-dev.json) | `dev` | No force-push/delete; PR + required `Test`; admin bypass. Back-merge CI pushes with `TAGTOKEN` |
| [`03-protect-release-hotfix.json`](03-protect-release-hotfix.json) | `release/*`, `hotfix/*` | Create/update/delete only via admin bypass |
| [`04-protect-release-tags.json`](04-protect-release-tags.json) | tags `v*` | Protect GitVersion / Release tags; create via admin / `TAGTOKEN` CI |
| [`05-push-block-secrets.json`](05-push-block-secrets.json) | push (repo-wide) | **Often org-only** — may fail import on personal repos |

## Bypass actors

| Actor | ID | Used for |
|---|---|---|
| RepositoryRole **Admin** | `5` | Owner (`denis-peshkov`) and workflows using an **admin PAT** (`TAGTOKEN`) |

**Do not** put Integration `15368` (GitHub Actions) in `bypass_actors` on this personal repo — import fails with:

```text
Error importing ruleset: The ruleset you are importing contains an invalid actor
```

Back-merge and tag push must use `secrets.TAGTOKEN` (owner PAT with `repo` scope), not `GITHUB_TOKEN`. Plain `GITHUB_TOKEN` is blocked by Protect-dev / Protect release tags (`GH013`).

**Tag push gotcha (same as back-merge):** `actions/checkout` can persist `GITHUB_TOKEN` as `http.https://github.com/.extraheader`, which overrides `git remote set-url` with `TAGTOKEN`. Tag push / back-merge use `persist-credentials: false` and unset that header before pushing with `TAGTOKEN`.

## After import

1. Open a test PR into `dev` — required check `Test` must appear.
2. Confirm non-admin cannot push to `master` / create `release/foo`.
3. Ensure Actions secret **`TAGTOKEN`** is set (owner PAT, `repo` scope) — same secret as `push-tags` / Homebrew / back-merge.
4. Run **Back-merge master to dev** once — must push to `dev` via `TAGTOKEN` (admin bypass; no PR, no build wait).
5. Optionally keep `branch-policy.yml` as a secondary signal.

## Not encoded in rulesets

- “Only owner may open PR to `master`” — use admin-only merge + `branch-policy.yml`, or require reviews from CODEOWNERS.
- Contributor branch prefixes `feature|fix|chore` — optional; add `branch_name_pattern` later in Evaluate mode.

## Push ruleset (05) — may not import on personal repos

GitHub may reject push rulesets on **personal** repositories. Keep `05-push-block-secrets.json` as a draft for a future org transfer, or rely on `.gitignore` + `branch-policy.yml`.
