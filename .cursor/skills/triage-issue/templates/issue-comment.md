# Issue Comment Templates

GitHub comments — **in English**. Resolve `{repository_name}` / `{repository_url}` from `gh repo view`.

---

## Template 1 — Acknowledgment + Request Info

```markdown
## Issue Triage

**Category**: {Bug | Feature | Enhancement | Question}
**Priority**: {P0 | P1 | P2 | P3}
**Effort estimate**: {XS | S | M | L | XL}

### Assessment

{1-2 sentences about the issue and why it matters for this library.}

### Missing Information

To move forward, we need:

- **Package / NuGet version** or git commit
- **Target framework** (e.g. net8.0)
- **Area** if relevant (from README / folder layout)
- **Reproduction steps** (no real passwords, tokens, or PII)

### Next Steps

{What happens after the info is provided.}

---
*Triaged via [{repository_name}]({repository_url}) Cursor `/triage-issue`*
```

---

## Template 2 — Duplicate

```markdown
## Duplicate Issue

This issue covers the same problem as #{original_number}: **{original_title}**.

### Overlap

{Explain overlap in 1-2 sentences.}

If your scenario differs materially, please reopen with that context. Otherwise, follow the original issue.

---
*Triaged via [{repository_name}]({repository_url}) Cursor `/triage-issue`*
```

---

## Template 3 — Close (Stale)

```markdown
## Closing: No Activity

This issue has been open for {N} days without activity. We're closing it to keep the backlog actionable.

If still relevant, reopen with your current package version, target framework, and reproduction steps.

---
*Triaged via [{repository_name}]({repository_url}) Cursor `/triage-issue`*
```

---

## Template 4 — Close (Out of Scope)

```markdown
## Closing: Out of Scope

After review, this request falls outside this repository’s current scope.

### Rationale

{Specific reason — e.g. app-specific UI, unrelated infrastructure.}

### Alternatives

{If applicable: extension points, sample host, or sibling packages.}

---
*Triaged via [{repository_name}]({repository_url}) Cursor `/triage-issue`*
```
