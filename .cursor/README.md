# `.cursor` — обзор

Каталог настроек Cursor для репозитория: правила, skills, triage/CI.

## Содержимое

| Путь | Назначение |
|---|---|
| [`rules/`](rules/) | Cursor Rules (`.mdc`) — стиль, архитектура, security, тесты |
| [`skills/`](skills/) | Agent skills (triage, release-plan, coderabbit, pr-message, …) |
| [`triage/`](triage/) | GitHub triage: `gh` wrapper, CI runners, отчёты |

Подробнее по triage: [`triage/docs/README.md`](triage/docs/README.md).
Каталог rules (только `.mdc`): [`rules/README.md`](rules/README.md).

## Триаж GitHub (issues / PRs)

- `.cursor/skills/triage/` — оркестратор issue + PR
- `.cursor/skills/triage-issue/` — GitHub issues
- `.cursor/skills/triage-pr/` — GitHub PRs (Phase 2 / review templates)
- `.cursor/triage/` — `gh-wrapper`, `collect-data.sh`, `post-pr-triage.mjs`

### Guidance для automated PR triage

`post-pr-triage.mjs` → `loadMatchedRules`:

1. Матчит `.cursor/rules/*.mdc` по frontmatter (`alwaysApply: true` или `globs` ↔ пути файлов PR).

Логика: [`triage/load-review-rules.mjs`](triage/load-review-rules.mjs).

## Skills (проект)

- `skills/triage/` — оркестратор issue + PR
- `skills/triage-issue/` — GitHub issues
- `skills/triage-pr/` — GitHub PRs
- `skills/release-plan/` — планы версий, `TO-DO.md`, `BREAKING.md`
- `skills/coderabbit/` — CodeRabbit CLI → текущий RELEASE-PLAN
- `skills/pr-message/` — текст PR по `.github/PULL_REQUEST_TEMPLATE.md` + авточеки
