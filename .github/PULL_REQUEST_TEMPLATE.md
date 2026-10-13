<!-- PR body: short narrative + minimal checklist. English only. -->

## Summary

<!-- What changed and why. Prefix the PR title with BREAKING: when needed. Add "Closes: #0000" if applicable. -->

Closes: #0000

---

## Changes

<!-- Extend `path/to/file.py` — numbered list; optional scope line at the end. -->

1. …
2. …

**Scope:** N files, ~N lines.

---

## Test plan

<!-- How you verified the change — check off before merge. -->

- [ ] New or updated tests cover the changed behavior
- [ ] `pytest` — green locally
- [ ] Manual UI check (if UI changed) — scan / results / delete as applicable

---

## Risks / notes

<!-- Required for delete/Recycle Bin behavior, packaging, or breaking changes. Otherwise write "N/A". -->

N/A

---

## Checklist

- [ ] I have read and followed [CONTRIBUTING.md](../CONTRIBUTING.md).
- [ ] There is no other open [pull request](https://github.com/denis-peshkov/duplicate-finder/pulls) for the same fix or feature.
- [ ] **One PR = one feature or one fix** — no unrelated refactors or drive-by formatting.
- [ ] `.editorconfig` / project Python style respected; no secrets committed.
- [ ] If this PR changes user-facing behavior or install docs, update README / `docs/` as needed.
- [ ] If this PR is breaking for users (settings, CLI, install paths), update [`docs/BREAKING.md`](../docs/BREAKING.md) when present and prefix the **PR title** with `BREAKING:`.
- [ ] If this PR touches delete / empty-folder cleanup or packaging, the risks are described above.

---

## AI assistance

- [ ] AI was used to generate or assist with this PR. *Describe briefly what AI helped with and what you manually verified.*

---

**License:** By opening this PR, you agree that contributions are under the [MIT License](../LICENSE.md).
