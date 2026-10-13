Ниже — **проблемы внутри библиотеки**, по уровню критичности. Аудит по дельте ветки относительно базовой ветки (обычно `master`).

> **Версия:** `2.0.0` · **ветка:** `release/big-improvements` · **база:** `origin/master` · **дата:** `2026-10-13`
>
> **Релиз (если есть):** https://github.com/denis-peshkov/duplicate-finder/releases/tag/v2.0.0
>
> **Легенда:** ⬜ open · ✅ done · 🟨 partial / принято · ❌ blocker
>
> **Предыдущий план:** —
>
> Дельта: `origin/master...HEAD` — **36** коммита · **111** файлов · **+10158 / −362**. Open: C0 H1 M2 L1

**CodeRabbit:**
- `2026-10-13` · pasted finding (GitVersion.yml:102 BranchName) · 1 finding (0 Critical, 0 Major, 1 Minor) → Open: C0 H1 M2 L1
- `2026-10-13` · pasted finding (coderabbit/SKILL.md:164 Phase 4 trigger) · 1 finding (0 Critical, 0 Major, 0 Minor; 1 Info) → Open: C0 H1 M2 L1
- `2026-10-13` · pasted finding (pr-message/triage-pr fetch swallow) · 1 finding (0 Critical, 0 Major, 1 Minor) → Open: C0 H1 M2 L1
- `2026-10-13` · pasted finding (resolve-target-version.sh:111–114 tag fallback) · 1 finding (0 Critical, 0 Major, 1 Minor) → Open: C0 H1 M2 L1
- `2026-10-13` · pasted finding (update-changelog.mjs:191 isLibraryPath .py) · 1 finding (0 Critical, 0 Major, 1 Minor) → Open: C0 H1 M2 L1
- `2026-10-13` · pasted finding (update-changelog.test.mjs:110–114 v2.3.0) · 1 finding (0 Critical, 0 Major, 1 Minor) → Open: C0 H1 M2 L1
- `2026-10-13` · pasted finding (triage-issue/SKILL.md:65 collaborators fallback) · 1 finding (0 Critical, 0 Major, 1 Minor) → Open: C0 H1 M2 L1
- `2026-10-13` · pasted finding (triage .NET leftovers → Python app) · 1 finding (0 Critical, 0 Major, 1 Minor) → Open: C0 H1 M2 L1
- `2026-10-13` · pasted finding (triage-pr/SKILL.md:85 statusCheckRollup) · 1 finding (0 Critical, 0 Major, 1 Minor) → Open: C0 H1 M2 L1
- `2026-10-13` · pasted finding (triage-pr/SKILL.md:145–148 origin/ strip) · 1 finding (0 Critical, 0 Major, 1 Minor) → Open: C0 H1 M2 L1
- `2026-10-13` · pasted finding (.editorconfig:9 utf-8-bom vs shebang) · 1 finding (0 Critical, 0 Major, 1 Minor) → Open: C0 H1 M2 L1
- `2026-10-13` · pasted finding (PULL_REQUEST_TEMPLATE.md relative links) · 1 finding (0 Critical, 0 Major, 1 Minor) → Open: C0 H1 M2 L1
- `2026-10-13` · pasted finding (rulesets required checks breaking-gate) · 1 finding (0 Critical, 0 Major, 1 Minor) → Open: C0 H1 M2 L1
- `2026-10-13` · pasted finding (protect-tags / push-tags TAGTOKEN vs GITHUB_TOKEN) · 1 finding (0 Critical, 0 Major, 1 Minor) → Open: C0 H1 M2 L1
- `2026-10-13` · pasted finding (rulesets README push-secrets fallback) · 1 finding (0 Critical, 0 Major, 0 Minor; 1 Info) → Open: C0 H1 M2 L1
- `2026-10-13` · pasted finding (breaking-gate.yml fork PR write token) · 1 finding (0 Critical, 1 Major, 0 Minor) → Open: C0 H1 M2 L1

**PR:** [#1](https://github.com/denis-peshkov/duplicate-finder/pull/1) (`BREAKING:` exe rename / `LICENSE.md` / `icon.png` / SemVer 2 / `clean_empty_folders` default).

---

## Критично (безопасность)

---

## Высокий (логика / licensing / auth model)

### ⬜ H1. Version substitution всё ещё за `publish_artifacts`

В `.github/actions/build-release-binary/action.yml` шаг **Set application version** остаётся под `if: inputs.publish_artifacts == 'true'`, хотя коммит/README заявляют подстановку **всегда** перед PyInstaller. `docs/ci-cd.md` описывает старое поведение. Нужно либо снять `if` у шага версии, либо вернуть README в соответствие с action.

---

## Средний (противоречия / баги контрактов)

### ⬜ M1. README SemVer-примеры устарели

Таблица Versioning в `README.md` всё ещё показывает `1.0.15` / `1.0.15-preview.3`, тогда как `GitVersion.yml` задаёт `next-version: 2.0.0` и целевой релиз — `2.0.0`.

### ⬜ M2. README Settings не описывает новые ключи

В дельте появились `include_masks`, `exclude_masks`, `clean_empty_folders` (defaults + UI + persistence), но секция Settings в README по-прежнему только путь к `settings.toml` / логу — без ключей и семантики масок / cleanup.

---

## Низкий (техдолг / несогласованности)

### ⬜ L1. `matches_exclude_mask` — тонкий alias

`matches_exclude_mask` в `src/core/enumerator.py` полностью делегирует в `matches_mask` («совместимость»). Либо убрать/свести вызовы, либо явно зафиксировать зачем нужен отдельный символ.

---

## Принято (осознанный trade-off)

- Major jump `1.0.14` → `2.0.0` через `GitVersion.yml` `next-version` (не patch/minor от 1.x).
- `clean_empty_folders = true` по умолчанию — cleanup пустых папок opt-out, не opt-in.
- Имя бинарника `DuplicateFinder` → `duplicate-finder` (kebab-case, едино с CLI shim).
- Логи и часть UI-строк переведены на English.
- GitVersion `feature`: `label: '{BranchName}'` + capture `(?<BranchName>.+)` в regex (как `useBranchName` в GV5).
- `resolve-target-version.sh`: `from_version` только stable `vX.Y.Z`; иначе синтетический `0.0.0` (не git tag); prerelease-fallback вырезан.
- triage-issue: при 403/404 collaborators fallback = авторы merged PR — осознанно (смерженный вклад = collaborator для triage).
- PR template: relative `../CONTRIBUTING.md` / BREAKING / LICENSE — оставляем (won't-fix абсолютные URL).

---

## Закрыто (проверено в коде)

| # | Суть |
|---|---|
| ✅ #H2 breaking-gate fork write | `pull_request_target` + checkout base only; fetch `pull/*/head` for diff; approval logic unchanged |
| ✅ #L3 rulesets README push-secrets | draft-only; fallback → secret scanning / push protection (не .gitignore / branch-policy) |
| ✅ #M15 push-tags TAGTOKEN vs checkout | `persist-credentials: false` + unset `.extraheader` before TAGTOKEN remote (как backmerge) |
| ✅ #M14 rulesets breaking-gate required | dismissed/reverted: admin bypass anyway; `breaking-gate` stays workflow-only (not required) |
| ✅ #M13 PR template relative links | dismissed: абсолютные blob-URL не хотим; relative оставлены |
| ✅ #M12 editorconfig charset | `[*]=utf-8`; BOM только `*.{cs,csproj,sln}` (shebang-safe) |
| ✅ #M11 origin/foo branch resolve | triage-pr: явный `origin/foo` → remote tip; local только для unprefixed `foo` |
| ✅ #M10 statusCheckRollup aggregate | triage-pr: CI clean/dirty/unstable по массиву checks, не `.state` |
| ✅ #M9 triage polyglot templates | issue/PR triage: detect .NET and/or Python; ask/review both when present |
| ✅ #M8 triage collaborators fallback | dismissed: merged PR author = collaborator для triage |
| ✅ #M7 collectDelta test tag | happy-path → существующий `v1.0.14` (не `v2.3.0`) |
| ✅ #M6 isLibraryPath .py | `update-changelog.mjs`: Library включает `.py` (+ .NET extensions) |
| ✅ #M5 resolve-target-version tag fallback | без preview-fallback; нет stable → `from_version=0.0.0` (+ changelog empty-tree) |
| ✅ #M4 Skills silent git fetch | pr-message + triage-pr named branch: fail fetch unless `offline` |
| ✅ #L2 CodeRabbit Phase 4 trigger | pasted finding / footer → только Phase 3; фикс только по явной просьбе |
| ✅ #M3 Feature BranchName capture | `regex` + `(?<BranchName>.+)`, `label: '{BranchName}'` |
| ✅ Include / exclude masks | Сканирование фильтруется `include_masks` / `exclude_masks` (UI `mask_list_panel`, enumerator `should_keep_file`, settings + тесты) |
| ✅ Empty-folder cleanup | `remove_empty_folders` + `resolve_empty_folder_roots`, прогресс/cancel, independent cleanup без выбранных файлов |
| ✅ Results Treeview | Кастомная таблица заменена на Treeview: сортировка, resize колонок, ellipsis |
| ✅ Two-list hash candidates | `_select_hash_candidates` хеширует только пересечение размеров между list1/list2 |
| ✅ Exe / Chocolatey rename | `duplicate_finder.spec`, `chocolateyinstall.ps1`, README assets → `duplicate-finder` |
| ✅ LICENSE.md / icon.png | `LICENSE`→`LICENSE.md`, `duplicate-finder-icon.png`→`icon.png`, nuspec URLs |
| ✅ GitVersion 6 / next 2.0.0 | Конфиг GV6, `next-version: 2.0.0`, digits в имени ветки игнорируются |
| ✅ CI hygiene | rulesets, breaking-gate, triage workflow, labels, issue/PR templates, backmerge |
| ✅ Test coverage | Расширены `test_deleter` / `test_enumerator` / `test_finder` / `test_hasher` / `test_settings` |

---

## Что в библиотеке уже нормально

- Маски: пустой include = все файлы; exclude отбрасывает матчи; дубликат маски в UI выбирается, а не копируется.
- Корни cleanup не удаляются; обход `os.walk(..., topdown=False)`; ошибки walk пишутся в `folders_failed`.
- Settings: неизвестные ключи TOML игнорируются; новые поля имеют defaults.
- Recycle Bin через `send2trash` и для файлов, и для пустых папок.

---

## Приоритет фиксов

1. **H1** — согласовать version substitution (action ↔ README ↔ ci-cd.md).
2. **M1** / **M2** — обновить README (SemVer-примеры + Settings keys).
3. **L1** — alias `matches_exclude_mask` (по желанию в этом релизе).

Кросс-релизная очередь: [`docs/TO-DO.md`](TO-DO.md).
