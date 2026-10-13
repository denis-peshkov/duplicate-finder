# Contributing to Duplicate Finder

Thank you for your interest in the project.

## Quick links

- [Report an issue](https://github.com/denis-peshkov/duplicate-finder/issues/new/choose)
- [Open PRs](https://github.com/denis-peshkov/duplicate-finder/pulls)
- [CI](https://github.com/denis-peshkov/duplicate-finder/actions/workflows/ci.yml)
- [CI (back-merge master → dev)](https://github.com/denis-peshkov/duplicate-finder/actions/workflows/backmerge-master-to-dev.yml)
- [Branch policy](https://github.com/denis-peshkov/duplicate-finder/actions/workflows/branch-policy.yml)
- [Breaking gate](https://github.com/denis-peshkov/duplicate-finder/actions/workflows/breaking-gate.yml)
- [Triage](https://github.com/denis-peshkov/duplicate-finder/actions/workflows/triage.yml)
- [SonarCloud](https://sonarcloud.io/summary/new_code?id=duplicate-finder)
- [README](README.md)
- [CI/CD](docs/ci-cd.md)
- [Distribution](docs/distribution.md)

---

## What is Duplicate Finder?

Desktop app (Python 3.12+, CustomTkinter) for finding and removing duplicate files:

- scan one path list or compare two lists;
- match by content or filename; optional image-only mode;
- include / exclude masks;
- optional empty-folder cleanup after delete (Recycle Bin via `send2trash`).

Packaging: GitHub Releases (PyInstaller), Chocolatey, Homebrew (core + preview tap). Details: [docs/distribution.md](docs/distribution.md).

---

## How you can help

| Type | Examples |
|---|---|
| **Report** | Bug with repro steps, OS, version, expected/actual |
| **Fix** | Scan/delete regression, UI glitch, packaging script bug |
| **Build** | New option, tests, docs |
| **Review** | PR review, especially delete flow and CI packaging |
| **Document** | README, `docs/ci-cd.md`, `docs/distribution.md` |

---

## Development principles

### Delete and data safety first

Changes to delete / Recycle Bin / empty-folder cleanup are **high-priority review**. Prefer clear UX and tests. Do not commit secrets, tokens, or private user paths in samples or issues.

### Minimal diff

Do not mix refactoring, formatting untouched files, and a feature in one PR. Drive-by changes belong in a separate PR.

### Repository conventions

- `.editorconfig` — style source.
- Python: follow [`.cursor/rules/python-pep8.mdc`](.cursor/rules/python-pep8.mdc) and [`.cursor/rules/python-naming.mdc`](.cursor/rules/python-naming.mdc).
- Tests — **pytest**; add/update tests with behavior changes.
- Layout: `main.py`, `src/` (`config`, `core`, `ui`, `utils`), `tests/`, `distribution/`, `.github/`.

---

## In scope / out of scope

### In scope

- `src/`, `main.py`, `tests/`;
- `duplicate_finder.spec`, packaging under `distribution/`;
- `README.md`, `docs/ci-cd.md`, `docs/distribution.md`;
- CI: `.github/workflows/ci.yml`, `branch-policy.yml`, `breaking-gate.yml`, `triage.yml`, `backmerge-master-to-dev.yml`.

### Out of scope (without maintainer discussion)

- Large architecture refactors “for aesthetics”;
- New external dependencies without a strong reason;
- User-breaking changes without a `BREAKING:` PR title (and `docs/BREAKING.md` when that file exists);
- Secrets, keys, `.env` in commits.

---

## Branches and releases

```
                        ┌──── CI merge ─────────┐     (master → dev, no PR)
feature/* ──┐           ▼                       │
fix/*     ──┼── PR ──► dev ── merge ──► master ─┴─► tags + Release + Chocolatey/Homebrew
chore/*   ──┘                              ▲
                                           │
                                 release/* / hotfix/* (owner only)
```

| Branch | Purpose | Who |
|---|---|---|
| `master` | Stable release; GitVersion, **stable** git tags, GitHub Release, Chocolatey, Homebrew | **Owner only** — direct push and PRs |
| `release/*` | Release preparation; preview packages; **no** git tags for pre-releases | **Owner only** |
| `hotfix/*` | Urgent production patches; same rules as `release/*` | **Owner only** |
| `dev` | Feature integration; **Default PR target** for contributors | Contributors via PR |
| `feature/*` | New functionality (build/test only) | Contributors |
| `fix/*` | Bug fixes (build/test only) | Contributors |
| `chore/*` | CI, deps, docs-only, maintenance | Contributors |

Git tags and GitHub Release run on **`master` only**. Preview Chocolatey / Homebrew preview tap: `release/*` / `hotfix/*`. Details: [docs/ci-cd.md](docs/ci-cd.md).

**Access rules (enforced via `.github/workflows/branch-policy.yml`):**

- Contributors open PRs **only into `dev`** from `feature/*`, `fix/*`, or `chore/*`.
- PRs targeting **`master`** — repository owner only (`denis-peshkov`).
- Pushing to **`master`**, **`release/*`**, or **`hotfix/*`** — owner only.
- After changes land on **`master`**, CI (`.github/workflows/backmerge-master-to-dev.yml`) **merges `master` into `dev` and pushes** using **`TAGTOKEN`**.

Optional GitHub Rulesets: import recipes from [`.github/rulesets/`](.github/rulesets/).

Versioning: **GitVersion** (`GitVersion.yml`). CI package version is `Major.Minor.run_number` (+ preview label on release/hotfix). `commit-message-incrementing: Disabled`.

---

## Branch naming

Prefix + kebab-case description:

| Prefix | When |
|---|---|
| `feature/` | New functionality |
| `fix/` | Bug fix |
| `chore/` | CI, deps, docs-only, maintenance |
| `release/` | Release preparation (owner) |
| `hotfix/` | Urgent production patch (owner) |

Examples:

```
release/1.1.0-masks-and-results-ui
hotfix/empty-folder-cleanup
feature/exclude-mask-docs
fix/results-sort-crash
chore/ci-gitversion-actions
```

---

## Commit messages

Use **clear English** messages in imperative/descriptive style:

```
Add include-mask enumerator tests
Fix empty-folder cleanup progress messaging
Update README Chocolatey install notes
```

For breaking changes, include `BREAKING:` in the PR title.

---

## Pull request process

### 1. Preparation

```bash
git checkout dev
git pull origin dev
git checkout -b feature/short-description
```

### 2. Changes

- Follow existing layout under `src/` and `tests/`.
- Do not touch unrelated files.
- Breaking user change → prefix PR title with `BREAKING:` (and update `docs/BREAKING.md` when present).

### 3. Tests (required)

See [Testing](#testing).

### 4. Open PR

- **Base branch:** `dev` (required for contributors)
- **Do not** open PRs into `master`, `release/*`, or `hotfix/*` unless you are the repository owner
- Description: what, why, how to verify (**English**)
- Breaking user change → prefix the **PR title** with `BREAKING:`
- CI detects `BREAKING:` title and/or a `docs/BREAKING.md` diff, adds `breaking-changes`, and **fails** until the owner adds `breaking-approved`

### 5. CI

Must pass:

- `CI` workflow (`.github/workflows/ci.yml`) — GitVersion, `pytest`, PyInstaller matrix
- Branch policy (`.github/workflows/branch-policy.yml`)
- `Breaking gate` when consumer-breaking — owner must add `breaking-approved`
- SonarCloud when `SONAR_TOKEN` is configured
- Triage PR comment job when enabled (`CURSOR_API_KEY`)

CodeRabbit (`.coderabbit.yaml`): comment `@coderabbitai full review` when a full pass is needed.

### 6. Review and merge

After approval — merge into `dev`. Release to `master` (tags, GitHub Release, Chocolatey, Homebrew) is a separate maintainer step.

### One PR rule

**One PR = one feature or one fix.** Split large changes (core + tests → UI → CI/docs).

---

## Testing

### Local setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

On macOS you also need Tk: `brew install python-tk@3.12`.

### Local run

```bash
pytest
python main.py
```

### Pre-PR checklist

- [ ] Tests added/updated for changed behavior
- [ ] `pytest` — green locally
- [ ] For delete / empty-folder / masks — prefer coverage beyond happy path
- [ ] No secrets in code or test data
- [ ] README / `docs/` updated when user-facing or packaging behavior changes

---

## Documentation

| What changed | Update |
|---|---|
| User-facing behavior / install | `README.md` |
| CI jobs / secrets / triggers | `docs/ci-cd.md` |
| Chocolatey / Homebrew / Release artifacts | `docs/distribution.md` |
| Breaking change for users | `docs/BREAKING.md` (when present) + `BREAKING:` PR title |

---

## License

Code is under the [MIT License](LICENSE). By contributing, you agree that contributions are licensed under the same terms.

There is no separate CLA — merging a PR means agreement with the repository license.

---

## Questions?

- Bugs and features: [GitHub Issues](https://github.com/denis-peshkov/duplicate-finder/issues)

**Thank you for contributing to Duplicate Finder.**
