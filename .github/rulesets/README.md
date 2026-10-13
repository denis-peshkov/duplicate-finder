# Duplicate Finder — GitHub Ruleset recipes

Importable JSON for [repository rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository), aligned with `CONTRIBUTING.md` branch policy.

Based on [github/ruleset-recipes](https://github.com/github/ruleset-recipes).

## Prerequisite

`duplicate-finder` is a **public** repository, so repository rulesets are available without GitHub Pro.

Until rulesets are imported and set to **Active**, keep enforcing policy via `.github/workflows/branch-policy.yml`.

## Import

1. Open the repo → **Settings** → **Rules** → **Rulesets**.
2. **New ruleset** → **Import a ruleset**.
3. Import files below **one by one** (table order = recommended import order).
4. Review each ruleset:
   - Confirm **status check** contexts: `Test` (job in `.github/workflows/ci.yml`) and, for **Protect dev** only, also `Branch policy` (job in `.github/workflows/branch-policy.yml`). Master already has `update` (admin-only merge/push) — required `Branch policy` there is redundant. If GitHub shows a different name (e.g. `CI / Test`), edit the required check after the first green run.
   - Confirm **Bypass** is Repository admin only (`RepositoryRole` / Admin).
5. Save with **Active** (or start with **Evaluate** if available on your plan).

## Files

| File | Target | Purpose |
|---|---|---|
| [`restrict-push-secrets.json`](restrict-push-secrets.json) | push (repo-wide) | **Often org-only** — may fail import on personal repos |
| [`protect-master.json`](protect-master.json) | `master` | No force-push/delete; PR + CI required; admin bypass for releases |
| [`protect-dev.json`](protect-dev.json) | `dev` | No force-push/delete; PR + required `Test` + `Branch policy`; admin bypass. Back-merge CI pushes with `TAGTOKEN` |
| [`protect-release-hotfix.json`](protect-release-hotfix.json) | `release/*`, `hotfix/*` | Create/update/delete only via admin bypass |
| [`protect-tags.json`](protect-tags.json) | tags `v*` | Protect GitVersion / Release tags; create via admin / `TAGTOKEN` CI |
| [`protect-homebrew-preview-tap.json`](protect-homebrew-preview-tap.json) | `homebrew-preview-tap` | CI-only formula branch; create/update/delete via admin / `TAGTOKEN` (no PR) |
| [`restrict-upstream-branch-creation.json`](restrict-upstream-branch-creation.json) | `~ALL` except official | Block create/update/delete of any other upstream branch (contributors use **forks**) |

## Bypass actors

| Actor | ID | Used for |
|---|---|---|
| RepositoryRole **Admin** | `5` | Owner (`denis-peshkov`) and workflows using an **admin PAT** (`TAGTOKEN`) |

**Do not** put Integration `15368` (GitHub Actions) in `bypass_actors` on this personal repo — import fails with:

```text
Error importing ruleset: The ruleset you are importing contains an invalid actor
```

Back-merge, tag push, and **homebrew-preview-tap** formula push must use `secrets.TAGTOKEN` (owner PAT with `repo` scope), not `GITHUB_TOKEN`. Plain `GITHUB_TOKEN` is blocked by Protect-dev / Protect tags / Protect homebrew-preview-tap (`GH013`).

**Tag / tap push gotcha (same as back-merge):** `actions/checkout` can persist `GITHUB_TOKEN` as `http.https://github.com/.extraheader`, which overrides `git remote set-url` with `TAGTOKEN`. Tag push / back-merge / preview-tap publish use `TAGTOKEN` (clone with token or `persist-credentials: false`) so the push authenticates as the owner PAT.

## After import

1. Open a test PR into `dev` **from a fork** (`feature/*`) — required checks `Test` and `Branch policy` must appear.
2. Confirm a same-repo or oddly named head PR into `dev` fails **Branch policy**.
3. Confirm non-admin cannot push to `master` / create `release/foo` / create `random/name`.
4. Ensure Actions secret **`TAGTOKEN`** is set (owner PAT, `repo` scope) — same secret as `push-tags` / Homebrew / back-merge.
5. Run **Back-merge master to dev** once — must push to `dev` via `TAGTOKEN` (admin bypass; no PR, no build wait).
6. Confirm non-admin cannot push to `homebrew-preview-tap`; a push from `release/*` CI (`publish-homebrew-tap` + `TAGTOKEN`) still updates the formula.

## Not encoded in rulesets (workflow instead)

- “Only owner may open PR to `master` / `release/*` / `hotfix/*`” — `branch-policy.yml` (+ admin merge).
- Contributor **fork** + head prefix `feature|fix|chore` on PRs into `dev` — `branch-policy.yml` (required check on Protect dev).
- Topic branches belong on forks; upstream create/update/delete of non-official names — `restrict-upstream-branch-creation.json`.

## Push ruleset — may not import on personal repos

GitHub may reject push rulesets on **personal** repositories. Keep `restrict-push-secrets.json` as a draft for a future org transfer, or rely on `.gitignore` + `branch-policy.yml`.
