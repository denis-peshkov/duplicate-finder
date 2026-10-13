# PR Review Comment Template

Comments in **English**. Resolve `{repository_name}` / `{repository_url}` from `gh repo view`.

```markdown
## Review

**Scope**: Security (secrets/auth/licensing), .NET quality, pipeline/registration, test coverage

### Summary

{1-2 sentences — main takeaway.}

### Critical Issues 🔴

{- `path/from/this-pr.cs:42` — problem, impact, suggested fix.}

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

- 🔴 Critical: security (secret leak, auth/licensing bypass), data loss, broken registration/pipeline, missing tests for security fix
- 🟠 Important: error handling gaps, breaking public API without docs, missing behavior tests
- 🟡 Suggestion: naming, DRY, documentation

## Checks (mention when relevant)

- No logging of secrets / license keys (see `.cursor/rules/*.mdc`)
- Auth/licensing/pipeline security (core and EF extension slots as designed)
- EF registration, transaction pipeline, and DbContext integration contracts
- `docs/BREAKING.md` / README / `config.nuspec` updated for public API or pack changes
- `*Tests*/` coverage for new behavior
- Multi-target `.csproj` ↔ nuspec alignment; `Nullable` / `Async` suffix / `.editorconfig` / BOM conventions

**Tone**: professional, constructive. 200–400 words.
