# CI/CD

Orchestrator: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)

Triggers: **push** (`master`, `release/*`, `hotfix/*`), **pull_request**, **workflow_dispatch**.

---

## Mermaid

```mermaid
flowchart TD
  subgraph triggers["Triggers"]
    T1["push: master, release/*, hotfix/*"]
    T2["pull_request"]
    T3["workflow_dispatch"]
  end

  V["version<br/>GitVersion"]
  TEST["test<br/>pytest"]

  subgraph matrix["release-binaries (matrix x 3)"]
    M1["windows-msvc · windows-latest"]
    M2["aarch64-macos · macos-latest"]
    M3["x86_64-macos · macos-15-intel"]
  end

  PT["push-tags<br/>master only"]
  CHR["publish-chocolatey"]
  HBT["publish-homebrew-tap<br/>release/hotfix"]
  REL["publish-release<br/>master only"]
  HB["publish-homebrew<br/>master only"]

  triggers --> V
  V --> TEST
  TEST --> matrix
  matrix --> PT
  matrix --> CHR
  TEST --> HBT
  PT --> REL
  REL --> HB
```

---

## Jobs

| Job | Runner | When | Role |
|-----|--------|------|------|
| `version` | ubuntu-latest | always | GitVersion → `version`, `channel`, `prerelease` |
| `test` | ubuntu-latest | after version | `pytest` |
| `release-binaries` | matrix Win/macOS | after test | PyInstaller; upload `release-binary-*` on push to release branches |
| `push-tags` | ubuntu-22.04 | push `master` | tags `v{version}`, `v{X.Y}`, `v{X}` |
| `publish-chocolatey` | windows-latest | push master/release/hotfix | pack + push `.nupkg` |
| `publish-homebrew-tap` | ubuntu-22.04 | push release/hotfix | branch `homebrew-preview-tap` |
| `publish-release` | ubuntu-22.04 | push `master` | GitHub Release + checksums |
| `publish-homebrew` | macos-latest | after release on `master` | homebrew-core PR / bump |

On release builds (`publish_artifacts=true`), CI patches `pyproject.toml` and `APP_VERSION` in `src/config/app_info.py` before PyInstaller.

---

## Secrets

| Secret | Used by |
|--------|---------|
| `TAGTOKEN` | `push-tags`, Homebrew fork / preview tap |
| `CHOCOLATEY_API_KEY` | `publish-chocolatey` |
| `HOMEBREW_GITHUB_API_KEY` | `publish-homebrew` (`brew bump-formula-pr` / PR) |

Pipeline distribution details: [distribution.md](distribution.md).
