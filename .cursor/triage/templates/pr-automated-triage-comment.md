# PR Automated Triage Comment Template

The agent fills JSON fields; `format-pr-comment.mjs` renders the layout (repository name and URL — from `gh repo view` / `GITHUB_REPOSITORY`).

**The markdown template body and JSON schema below are in English** (GitHub / CI posts are always EN; the agent `summary` is EN as well).

```markdown
> **{repository_name}** · Automated triage by AI
> _(optional icon when `TRIAGE_ICON_REL_PATH` is set, e.g. `icon.png`)_

## 🔍 Automated Triage

| | |
|---|---|
| ✨ **Category** | `{category}` |
| {priority_emoji} **Priority** | `{priority}` |
| 🎯 **Confidence** | {confidence}% |

### Summary

{summary}

{maintainer_hint_block}

<details>
<summary>📁 Relevant files</summary>

{relevant_files_list}

</details>

{security_block}

---
*Triaged automatically by [{repository_name}]({repository_url}) · [Cursor](https://cursor.com)* · This is an automated analysis, not a human review.
<!-- triage -->
```

## JSON schema (agent output)

```json
{
  "category": "feature|bug|enhancement|security|docs|chore",
  "priority": "critical|high|medium|low",
  "confidence": 85,
  "summary": "2-4 sentences in English.",
  "maintainerHint": "Optional one-line hint, e.g. simple fix / needs security review",
  "relevantFiles": ["path/from/this-pr.cs"],
  "securityNotes": "Optional; omit if N/A"
}
```

## Category / priority rules

- **security** + **critical/high** for secret leaks, auth/licensing bypass, token misuse, PII exposure, payment issues
- **bug** for regressions and failing tests
- **feature** for new API or behavior
- **enhancement** for polish/perf/DX without new public contract

## GitHub labels (CI)

After analysis, `post-pr-triage.mjs` syncs PR labels via `apply-pr-labels.mjs`:

| Field | Label |
|---|---|
| `category` | `feature` / `bug` / `enhancement` / `security` / `docs` / `chore` |
| `priority` | `priority:critical` / `priority:high` / `priority:medium` / `priority:low` |

Only these managed labels are added/removed; other PR labels are kept. Missing labels are created with `--force`.
