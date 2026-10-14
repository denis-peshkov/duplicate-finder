# Finalize reply (agent → user)

Fill placeholders after **Finalize version plan** steps 1–9. Do **not** restate the full workflow here.

Language: same as the skill body (RU). Keep the reply short.

```markdown
План **`{{VERSION}}` закрыт** (finalized).

**Leftovers → TO-DO:** {{LEFTOVERS_OR_NONE}}

**Принято → TO-DO:** {{ACCEPTED_SYNC_SUMMARY}}

**Id high-water:** `C{{HW_C}}` `H{{HW_H}}` `M{{HW_M}}` `L{{HW_L}}`

**План:** [`docs/RELEASE-PLAN-{{VERSION}}.md`](docs/RELEASE-PLAN-{{VERSION}}.md) — `{{VERSION}} ({{CLOSED_LABEL}})`, C/H/M/L пустые, Принято/Закрыто сохранены

{{OPTIONAL_PUBLISH_NOTE}}
```

## Placeholders

| Placeholder | Fill with |
|---|---|
| `{{VERSION}}` | SemVer without `v` (e.g. `2.4.0`) |
| `{{LEFTOVERS_OR_NONE}}` | Comma-separated open ids moved to TO-DO (`H18, M79`), or `нет (open C/H/M/L уже были пустые)` |
| `{{ACCEPTED_SYNC_SUMMARY}}` | Short note: count + topics synced into TO-DO «Принято», or `без изменений (уже были)` / `нет новых` |
| `{{HW_C}}` `{{HW_H}}` `{{HW_M}}` `{{HW_L}}` | New TO-DO Id high-water integers after finalize |
| `{{CLOSED_LABEL}}` | `published / closed` if GitHub release/tag exists; else `closed` |
| `{{OPTIONAL_PUBLISH_NOTE}}` | One short note if tag/PR/publish still pending; otherwise omit the whole line |

## Rules

- Reply **only** in this shape (plus at most one clarifying sentence if the user must act next).
- Do **not** paste full «Принято» / «Закрыто» tables into the chat.
- In chat, link the plan as repo-root `docs/RELEASE-PLAN-X.Y.Z.md` (not a path relative to this template file).
