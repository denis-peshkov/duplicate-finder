# PR Review Comment Template

Comments in **English**. Resolve `{repository_name}` / `{repository_url}` from `gh repo view`.

Detect stack from the PR delta / repo (`.csproj` / `.sln` → .NET; `pyproject.toml` / `*.py` / PyInstaller `.spec` → Python). Fill **Scope** and checks for **every** stack present (dual-stack OK).

```markdown
## Review

**Scope**: Security (secrets/auth/licensing); { .NET quality, DI/pipeline/registration | Python app quality (core/UI/packaging) | both }; test coverage; docs/CI as touched

### Summary

{1-2 sentences — main takeaway.}

### Critical Issues 🔴

{- `path/from/this-pr.ext:42` — problem, impact, suggested fix.}

{If none: "None found."}

### Important Issues 🟠

{Significant issues with file:line citations.}

{If none: "None found."}

### Suggestions 🟡

{Nice-to-haves. Omit section if none.}

### What's Good ✅

{At least one specific positive point.}

---
*Automated review via [{repository_name}]({repository_url}) Cursor `/triage-pr`*
```

## Severity

- 🔴 Critical: security (secret leak, auth/licensing bypass), data loss, broken core pipeline/registration or destructive user flows, missing tests for security/data-loss fix
- 🟠 Important: error handling gaps, breaking public API / user-facing behavior without docs, missing behavior tests
- 🟡 Suggestion: naming, DRY, documentation

## Checks (mention when relevant)

**Any stack**

- No logging of secrets / license keys / private paths (see `.cursor/rules/*.mdc`)
- `docs/BREAKING.md` / README updated for user-breaking or pack/install changes
- Tests for new behavior (`*Tests*/` and/or `tests/`)

**.NET** (if present in delta)

- Auth/licensing/pipeline security; EF registration / DbContext contracts when touched
- Multi-target `.csproj` ↔ nuspec alignment; `Nullable` / `Async` suffix / `.editorconfig` / BOM conventions

**Python** (if present in delta)

- Core / UI / settings contracts; delete/Recycle Bin / empty-folder safety when touched
- Packaging: PyInstaller / Chocolatey / Homebrew paths and names stay consistent
- `pytest` coverage for changed behavior

**Tone**: professional, constructive. 200–400 words.
