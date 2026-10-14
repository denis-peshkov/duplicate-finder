# Breaking changes

Consumer-facing changes between published versions of duplicate-finder. Newest first.

| Range | Section |
|-------|---------|
| `1.0.14` → `2.0.0+` | [From 1.0.14 to 2.0.0](#from-1014-to-200) |

---

## From 1.0.14 to 2.0.0

Release: [v2.0.0](https://github.com/denis-peshkov/duplicate-finder/releases/tag/v2.0.0) ([PR #1](https://github.com/denis-peshkov/duplicate-finder/pull/1)).

### Binary / install names

- PyInstaller and release-archive executable renamed: `DuplicateFinder.exe` / `DuplicateFinder` → `duplicate-finder.exe` / `duplicate-finder`. Update shortcuts, scripts, and any Chocolatey/`Install-BinFile` consumers that still point at the old file name. The shim name `duplicate-finder` is unchanged.

### Repository file paths

- License file: `LICENSE` → `LICENSE.md`.
- Project icon: `duplicate-finder-icon.png` → `icon.png` (Chocolatey `iconUrl` follows `icon.png` on `master`).

### SemVer

- Version line jumps from the `1.0.x` series to **`2.0.0`** (`GitVersion.yml` `next-version`). Pins and automation that expect `1.x` must retarget.

### Defaults

- New setting `clean_empty_folders` defaults to **`true`**: after delete (or alone, with no files selected), empty folders under the target list roots may be moved to the Recycle Bin unless the Results checkbox is cleared.
