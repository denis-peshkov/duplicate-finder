Ниже — **проблемы внутри библиотеки**, по уровню критичности. Аудит по дельте ветки относительно базовой ветки (обычно `master`).

> **Версия:** `{{VERSION}}` · **ветка:** `{{BRANCH}}` · **база:** `{{BASE}}` · **дата:** `{{DATE}}`
>
> **Релиз (если есть):** {{REPOSITORY_LINK}}/releases/tag/v{{VERSION}}
>
> **Легенда:** ⬜ open · ✅ done · 🟨 partial / принято · ❌ blocker
>
> **Предыдущий план:** {{PREVIOUS_PLAN_LINK_OR_DASH}}
>
> Дельта: `{{BASE}}...HEAD` — **{{DELTA_COMMITS}}** коммита · **{{DELTA_FILES}}** файлов · **{{DELTA_PLUS}} / {{DELTA_MINUS}}**. {{OPEN_CHML_STATUS}}

**CodeRabbit:**
- `{{CR_DATE}}` · log `{{CR_LOG_PATH}}` · {{CR_FINDINGS_COUNT}} findings ({{CR_CRITICAL}} Critical, {{CR_MAJOR}} Major, {{CR_MINOR}} Minor) → {{CR_CURRENT_STATUS}}.

**PR:** {{PR_LINE_OR_DASH}}

---

## Критично (безопасность)

{{CRITICAL_OR_EMPTY}}

---

## Высокий (логика / licensing / auth model)

{{HIGH_OR_EMPTY}}

---

## Средний (противоречия / баги контрактов)

{{MEDIUM_OR_EMPTY}}

---

## Низкий (техдолг / несогласованности)

{{LOW_OR_EMPTY}}

---

## Принято (осознанный trade-off)

{{ACCEPTED_OR_EMPTY}}

---

## Закрыто (проверено в коде)

| # | Суть |
|---|---|
| ✅ #{{CLOSED_ID}} {{CLOSED_TITLE}} | {{CLOSED_SUMMARY}} |

---

## Что в библиотеке уже нормально

{{ALREADY_OK_BULLETS}}

---

## Приоритет фиксов

{{PRIORITY_OR_EMPTY}}
