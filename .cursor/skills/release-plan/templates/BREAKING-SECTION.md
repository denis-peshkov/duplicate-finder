# Сниппет секции BREAKING (для мейнтейнеров)

Правила, скрипты, workflow: skill [`release-plan`](../SKILL.md) → **`docs/BREAKING.md`**.

| Placeholder | Значение |
|---|---|
| `{{REPOSITORY_LINK}}` | Базовый URL GitHub-репо, напр. `https://github.com/org/repo` |
| `{{PR_NUMBER}}` | Id PR, когда известен (до тех пор опускать `([PR #…](…)).`) |

```markdown
---

## From {{FROM_VERSION}} to {{TO_VERSION}}

Release: [v{{TO_VERSION}}]({{REPOSITORY_LINK}}/releases/tag/v{{TO_VERSION}}) ([PR #{{PR_NUMBER}}]({{REPOSITORY_LINK}}/pull/{{PR_NUMBER}})).

{{BODY}}
```

Предпочитать `scaffold-breaking-section.sh` — заполняет `{{REPOSITORY_LINK}}` из `git remote` + resolved version.
