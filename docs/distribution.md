# Distribution

Desktop app distribution for **Duplicate Finder**: GitHub Releases, Chocolatey, Homebrew (core + preview tap).

Pipeline overview: [ci-cd.md](ci-cd.md).

## CI actions

Orchestrator: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

On each **push** to `master`, `release/*`, or `hotfix/*`:

- **`push-tags`** — **`master` only**
- **`publish-chocolatey`** — master / release / hotfix
- **`publish-homebrew-tap`** — release / hotfix only
- **`publish-release`** — after tags on **`master`**
- **`publish-homebrew`** — after GitHub Release on **`master`**

| Composite action | What it publishes |
|------------------|-------------------|
| [`push-tags`](../.github/actions/push-tags/action.yml) | Git tags (`master` only) |
| [`publish-release`](../.github/actions/publish-release/action.yml) | GitHub Release assets (`master` only) |
| [`publish-chocolatey`](../.github/actions/publish-chocolatey/action.yml) | chocolatey.org `.nupkg` (embedded Windows exe) |
| [`publish-homebrew`](../.github/actions/publish-homebrew/action.yml) | homebrew-core formula PR / bump (`master` only) |
| [`publish-homebrew-tap`](../.github/actions/publish-homebrew-tap/action.yml) | Preview formula on `homebrew-preview-tap` |

Upstream:

| Composite action | Role |
|------------------|------|
| [`version`](../.github/actions/version/action.yml) | GitVersion |
| [`test`](../.github/actions/test/action.yml) | pytest |
| [`build-release-binary`](../.github/actions/build-release-binary/action.yml) | PyInstaller matrix; `release-binary-*` artifacts |

## GitHub Release assets

Published by `publish-release`:

| Asset | Platform |
|-------|----------|
| `duplicate-finder-{version}-src.tar.gz` | Full source (Homebrew) |
| `duplicate-finder-{version}-x86_64-pc-windows-msvc.zip` | Windows x64 (`DuplicateFinder.exe`) |
| `duplicate-finder-{version}-aarch64-apple-darwin.tar.gz` | macOS Apple Silicon |
| `duplicate-finder-{version}-x86_64-apple-darwin.tar.gz` | macOS Intel |
| `SHA256SUMS` | Checksums |

## Chocolatey

```powershell
choco install duplicate-finder
```

Package id: `duplicate-finder`. Template: [`distribution/chocolatey/duplicate-finder/`](../distribution/chocolatey/duplicate-finder/).

CI embeds `DuplicateFinder.exe` and registers PATH shim `duplicate-finder` via `Install-BinFile`.

Secret: `CHOCOLATEY_API_KEY`.

## Homebrew (homebrew-core)

```bash
brew install duplicate-finder
```

Works after the formula is merged into [Homebrew/homebrew-core](https://github.com/Homebrew/homebrew-core) as `Formula/d/duplicate-finder.rb`.

Draft: [`distribution/homebrew-core/duplicate-finder.rb`](../distribution/homebrew-core/duplicate-finder.rb).

Python deps are declared as PyPI `resource` blocks (`url` + `sha256` from [PyPI JSON](https://warehouse.pypa.io/api-reference/json.html)); install uses `virtualenv_install_with_resources`. After changing app dependencies, refresh resources (e.g. `brew update-python-resources` against a local tap copy, or regenerate from PyPI metadata).

Secrets: `TAGTOKEN`, `HOMEBREW_GITHUB_API_KEY` (classic PAT with `public_repo`).

## Homebrew preview tap

From `release/*` / `hotfix/*` — **no git tag**. CI updates `Formula/duplicate-finder-preview.rb` on branch **`homebrew-preview-tap`**.

```bash
brew tap denis-peshkov/duplicate-finder https://github.com/denis-peshkov/duplicate-finder --branch homebrew-preview-tap
brew install duplicate-finder-preview
```

Draft: [`distribution/homebrew-preview/`](../distribution/homebrew-preview/).
