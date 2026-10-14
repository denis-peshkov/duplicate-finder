# Changelog

All notable changes to duplicate-finder are documented here (newest first).
GitHub Releases: https://github.com/denis-peshkov/duplicate-finder/releases

---

## v2.0.0 — 13 Oct 2026

### CI / release process

- GitHub rulesets for `master`, `dev`, `release`/`hotfix`, release tags, secret push-block, and `homebrew-preview-tap`.
- Added `breaking-gate`, `branch-policy`, `backmerge-master-to-dev`, and automated PR triage workflows.
- Issue/PR templates, label snapshot (`LABELS.yml` / `LABELS.md`), and Chocolatey publish/verification path updates for `duplicate-finder` / `icon.png`.
- PyInstaller artifact name standardized to `duplicate-finder` (Windows `.exe` / Linux / macOS binary).
- CI release matrix includes Linux x64 (`x86_64-unknown-linux-gnu` tar.gz on GitHub Releases).

### Versioning

- GitVersion 6.x config: `next-version: 2.0.0`, branch-name digits ignored, ContinuousDeployment on `main`/`master`.
- Major line jump from published `1.0.14` to `2.0.0` (see `docs/BREAKING.md`).

### Library

- Include and exclude filename/path masks for scanning (`include_masks` / `exclude_masks`), with UI panels and settings persistence.
- Optional empty-folder cleanup after delete (or alone): progress, cancel, root resolution by search/delete mode; default `clean_empty_folders = true`.
- Results page rewritten onto Treeview (sortable/resizable columns, ellipsized paths).
- Faster exact-hash path: hash only size-intersecting candidates across two lists.
- Logging and several UI strings standardized to English.
- License file renamed to `LICENSE.md`; project icon to `icon.png`.

### Tests

- Expanded coverage for masks, empty-folder deletion (walk errors, cancel, progress), hash candidates, hasher, and settings round-trip.

### Documentation

- README / `docs/ci-cd.md` / `docs/distribution.md` aligned to Python/`pytest`, new exe names, and `2.x` release line.
- Added `docs/BREAKING.md` (From 1.0.14 to 2.0.0) and this changelog.
- `CONTRIBUTING.md` and maintainer Cursor skills (release-plan, triage, CodeRabbit).

### Repository tooling

- `.editorconfig`, `.gitattributes`, `.coderabbit.yaml`, Cursor rules/skills, and local triage scripts under `.cursor/triage/`.

---

## v1.0.14 — 3 Sep 2026

[GitHub Release](https://github.com/denis-peshkov/duplicate-finder/releases/tag/v1.0.14) · compare [`v1.0.13...v1.0.14`](https://github.com/denis-peshkov/duplicate-finder/compare/v1.0.13...v1.0.14)

### Documentation

- README: added SonarCloud coverage badge.

---

## v1.0.13 — 3 Sep 2026

[GitHub Release](https://github.com/denis-peshkov/duplicate-finder/releases/tag/v1.0.13) · compare [`v1.0.7...v1.0.13`](https://github.com/denis-peshkov/duplicate-finder/compare/v1.0.7...v1.0.13)

### CI / release process

- Integrated SonarCloud scan into the test composite action / CI workflow.
- Switched to the SonarQube scan action; clarified project key / name formatting and made `SONAR_TOKEN` mandatory.
- Checkout `fetch-depth: 0` for accurate Sonar analysis.

### Tests

- Moved `pytest-cov` into `pyproject.toml` `[project.optional-dependencies] dev` (removed a redundant install step).

### Documentation

- `docs/ci-cd.md`: documented SonarCloud in the test job and secrets table.

### Repository tooling

- `.gitignore`: coverage / Sonar-related artifacts.

---

## v1.0.7 — 3 Sep 2026

[GitHub Release](https://github.com/denis-peshkov/duplicate-finder/releases/tag/v1.0.7) · compare from initial history (release notes also referenced `v0.1.6`, which is not retained as a git tag)

First published `1.0.x` line on GitHub. Highlights from the commits leading to this tag:

### Library

- Desktop duplicate finder (CustomTkinter): single-list and two-list search, exact hash and same-filename modes, images-only filter, Recycle Bin deletion via `send2trash`.
- Progress and delete-progress windows with elapsed / estimated time.
- About window with app metadata, license, and links; contextual help dialogs.
- `partial_hash` hardened against `OSError`.
- Path display / word-wrap fixes in results UI.

### CI / release process

- Chocolatey packaging enabled.
- Homebrew formulas added (Python 3.12, `python-tk`, virtualenv resources); CI macOS runner versions adjusted.
- GitVersion `next-version` set to `1.0.0` for the `1.x` line.

### Documentation

- English README; `docs/ci-cd.md` and `docs/distribution.md`.
- README badge icons (GitHub light/dark) and Chocolatey icon metadata.

---
