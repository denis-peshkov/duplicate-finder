# Cross.DataFilter — лейблы GitHub

Снимок настроенных лейблов репозитория. Машиночитаемый файл: [`LABELS.yml`](LABELS.yml).

Восстановление / sync (локальный файл → GitHub):

```bash
# create/update from LABELS.yml
while IFS= read -r name; do
  color=$(yq -r ".[] | select(.name==\"$name\") | .color" .github/LABELS.yml)
  desc=$(yq -r ".[] | select(.name==\"$name\") | .description" .github/LABELS.yml)
  gh label create "$name" --color "$color" --description "$desc" --force
done < <(yq -r '.[].name' .github/LABELS.yml)
```

## Triage (ставит на PR автоматически)

Один **category** + один **priority** (если confidence ≥ 70).

### Categories

| # | Категория | Почему выше |
|---|---|---|
| 1 | security | Утечки/auth/лицензия → всегда security + high/critical |
| 2 | bug | Регрессии и падения важнее «новой фичи» |
| 3 | feature | Новое API/поведение важнее polish/docs |
| 4 | enhancement | Polish / perf / DX без нового публичного контракта |
| 5 | docs | Доработки / дополнения документации |
| 6 | chore | CI/tooling/deps без продуктового эффекта |

**Как читать смешанный PR:** берёшь все подходящие категории по диффу, оставляешь **самую верхнюю** из таблицы.

Priority (`critical`…`low`) — **отдельная ось**, не путать с лестницей категорий.

---

### Приоритет — «насколько срочно»

| Лейбл | По-русски |
|---|---|
| `priority:critical` | Критично (блокер / срочно) |
| `priority:high` | Высокий |
| `priority:medium` | Средний |
| `priority:low` | Низкий |

---

## All labels

| Label | Color | Description (GitHub) | По-русски | Triage |
|---|---|---|---|---|
| `breaking-approved` | `#0e8a16` | Owner approved consumer-breaking change (unblocks breaking-gate) | Owner одобрил breaking (снимает blocking gate) | — |
| `breaking-changes` | `#b60205` | Consumer-breaking signals detected (BREAKING: title and/or docs/BREAKING.md) | Обнаружены consumer-breaking сигналы (ставит CI) | — |
| `bug` | `#e8372a` | Something is broken | Что-то сломано / дефект | category |
| `chore` | `#1d76db` | Build, CI, tooling, deps | Сборка, CI, tooling, зависимости | category |
| `docs` | `#006b75` | Improvements or additions to documentation | Доработки / дополнения документации | category |
| `duplicate` | `#ffffff` | This issue or pull request already exists | Такой issue/PR уже есть | — |
| `enhancement` | `#a2eeef` | Polish, perf, or DX without new public contract | Polish / perf / DX без нового публичного контракта | category |
| `feature` | `#0e8a16` | New API or behavior | Новое API или поведение | category |
| `help wanted` | `#008672` | Extra attention is needed | Нужна помощь со стороны | — |
| `invalid` | `#fef2c0` | This doesn't seem right | Некорректно / не по делу | — |
| `priority:critical` | `#b60205` | Triage priority: critical | Приоритет triage: критично | priority |
| `priority:high` | `#d93f0b` | Triage priority: high | Приоритет triage: высокий | priority |
| `priority:low` | `#fbca04` | Triage priority: low | Приоритет triage: низкий | priority |
| `priority:medium` | `#fb8500` | Triage priority: medium | Приоритет triage: средний | priority |
| `question` | `#d876e3` | Further information is requested | Нужны уточнения / вопрос | — |
| `security` | `#5319e7` | 🔒 Secrets, licensing, PII, or unsafe filter/query handling | Безопасность: секреты, лицензия, ПДн, опасные фильтры | category |
| `wontfix` | `#080808` | This will not be worked on | Не будем делать | — |
