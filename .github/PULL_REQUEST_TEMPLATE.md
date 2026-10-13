<!-- PR body: short narrative + minimal checklist. English only. -->

## Summary

<!-- What changed and why. Prefix the PR title with BREAKING: when needed. Add "Closes: #0000" if applicable. -->

Closes: #0000

---

## Changes

<!-- Extend `path/to/file.cs` — numbered list; optional scope line at the end. -->

1. …
2. …

**Scope:** N files, ~N lines.

---

## Test plan

<!-- How you verified the change — check off before merge. -->

- [ ] New or updated tests cover the changed behavior
- [ ] `dotnet build Cross.CQRS.EF.slnx` — green locally
- [ ] `dotnet test Cross.CQRS.EF.Tests/Cross.CQRS.EF.Tests.csproj` — green locally

---

## Risks / notes

<!-- Required for licensing, DI registration, transactions, or breaking changes. Otherwise write "N/A". -->

N/A

---

## Checklist

- [ ] I have read and followed [CONTRIBUTING.md](../CONTRIBUTING.md).
- [ ] There is no other open [pull request](https://github.com/denis-peshkov/Cross.CQRS.EF/pulls) for the same fix or feature.
- [ ] **One PR = one feature or one fix** — no unrelated refactors or drive-by formatting.
- [ ] `.editorconfig` respected; no secrets committed.
- [ ] If this PR changes public API or registration, update README / XML docs as needed.
- [ ] If this PR is breaking for NuGet consumers, update [`docs/BREAKING.md`](../docs/BREAKING.md) (nuspec keeps a link, not a duplicate list) and prefix the **PR title** with `BREAKING:`.
- [ ] If this PR touches licensing or transactions, the risks are described above and the diff contains no secrets.

---

## AI assistance

- [ ] AI was used to generate or assist with this PR. *Describe briefly what AI helped with and what you manually verified.*

---

**License:** By opening this PR, you agree that contributions are under [RPL 1.5](../LICENSE.md) (or [Peshkov commercial license](https://peshkov.biz/license) where applicable).
