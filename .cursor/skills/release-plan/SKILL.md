---
name: release-plan
description: >-
  Строит или обновляет docs/RELEASE-PLAN-X.Y.Z.md по текущей ветке относительно
  master (только delta). Переносит оставшиеся открытые пункты предыдущего плана
  в docs/TO-DO.md (open C/H/M/L + кросс-версионное «Принято»). Закрытие/отклонение
  пункта TO-DO всегда сначала добавляет `✅ #Id …` в «Закрыто» текущего плана,
  затем удаляет из open-секций TO-DO.
  Финализация version plan переносит все оставшиеся open-пункты в TO-DO и
  переписывает план по finalized-шаблону. Также ведёт исторический чеклист
  → master (docs/RELEASE-PLAN-to-master.md) через
  scripts/release-plan-to-master.mjs. Использовать при черновике release notes,
  release plans, закрытии version plan или обновлении RELEASE-PLAN-X.Y.Z.md /
  TO-DO.md / BREAKING.md / чеклиста to-master.
---

# Release plan по delta ветки

## Когда использовать

- Пользователь просит **release notes / RELEASE-PLAN** для текущей ветки относительно `master`
- Обновить `docs/RELEASE-PLAN-X.Y.Z.md` для планируемой или выпускаемой версии
- Синхронизировать открытый backlog в [`docs/TO-DO.md`](../../../docs/TO-DO.md)
- Файл текущего version plan **отсутствует** и его нужно создать, прежде чем другая работа сможет в него писать
- Пользователь просит **закрыть / финализировать / ship** version plan (open leftovers → TO-DO, план → finalized shape)

## Cross-skill references

Другие skills **не** копируют workflow отсюда — одна строка, **одинаковый** формат:

```text
Skill [`release-plan`](SKILL.md) → **Section** · domain hint
```

| Section (заголовок в этом файле) | Типичный domain hint |
|---|---|
| **Ensure current RELEASE-PLAN** | напр. CR findings → plan, не TO-DO |
| **`docs/BREAKING.md`** | напр. имена скриптов / текст миграции |
| **Close from TO-DO** | dismiss / won’t-fix |
| **Re-check** | закрыть open-пункт в version plan |
| **Finalize version plan** | ship / leftovers → TO-DO |
| **Previous plans published/closed** | `(closed)` → `(published / closed)` если есть tag |
| **Локальный `dotnet test`** | локальный прогон тестов |

Из sibling skills — относительная ссылка: `[`release-plan`](../release-plan/SKILL.md)`.

**Нумерация workflow:** фазы `### Phase N — …` (под `## Workflow`, или `## Phase N` для оркестраторов). Нумерованные шаги **только если в фазе 2 и более равноправных шагов**; одношаговая фаза = проза сразу под заголовком (без одиночного `1.`). **Без** обёртки `1.` с вложенным подсписком — один плоский список или проза.

## Два файла version plan

| Файл | Содержимое |
|---|---|
| `docs/RELEASE-PLAN-X.Y.Z.md` | **Только** delta этого релиза относительно базы (`master`) |
| `docs/TO-DO.md` | Кросс-версионный **открытый** backlog (C/H/M/L) + **Принято** (durable trade-offs); инкрементально |

В шапке плана: **Предыдущий план** — ссылка **только на непосредственно предыдущий** `docs/RELEASE-PLAN-A.B.C.md` (последний по версии ниже текущего). **Не** перечислять всю цепочку. Если предыдущего нет — `—`.

**Запрещено** в теле version plan ссылаться на **более новую** версию / `RELEASE-PLAN` с большим SemVer (закрытие «в следующем релизе», «см. 10.0.0», …). Факт закрытия позже — только в плане той версии, где закрыли, или в `TO-DO.md`.

## Каноническая форма (version plan)

**Источник истины по структуре:**
- Активный (открытая работа): [`templates/RELEASE-PLAN.md`](templates/RELEASE-PLAN.md)
- Закрытый / finalized: [`templates/RELEASE-PLAN-FINALIZED.md`](templates/RELEASE-PLAN-FINALIZED.md)
- Ответ пользователю после finalize: [`templates/FINALIZE-REPLY.md`](templates/FINALIZE-REPLY.md)
- Новый блок `docs/BREAKING.md` **From X → Y**: workflow в **`docs/BREAKING.md`** ниже; сниппет [`templates/BREAKING-SECTION.md`](templates/BREAKING-SECTION.md)

Общий placeholder: **`{{REPOSITORY_LINK}}`** — базовый URL GitHub-репо из `git remote` (`resolve-target-version.sh` → `repository_link`; fallback в `scripts/lib/repository-link.sh`).

Заполнить placeholders → записать `docs/RELEASE-PLAN-X.Y.Z.md`. **Не** хардкодить конкретные имена файлов версий в этом skill.

**Шапка — `Релиз (если есть):`** — `{{REPOSITORY_LINK}}/releases/tag/v{{VERSION}}` (не `—`; `{{REPOSITORY_LINK}}` из `git remote`, см. `resolve-target-version.sh` → `repository_link`).

**Шапка — хвост (после «Предыдущий план»):**

1. **Дельта** (в `>` blockquote, после пустой `>`):
   `Дельта: \`{{BASE}}...HEAD\` — **{{N}}** коммита · **{{F}}** файлов · **{{+X}} / {{−Y}}**. {{OPEN_CHML_STATUS}}`
   - Считать: `git rev-list --count {{BASE}}...HEAD`, `git diff --shortstat {{BASE}}...HEAD`.
   - `{{OPEN_CHML_STATUS}}`: `Open C/H/M/L пустые.` **или** `Open: Cx Hy Mz Lw`.
2. **CodeRabbit** (вне blockquote; список bullets под одним заголовком; если не гоняли — один bullet `не запускался.` / `—`):

```markdown
**CodeRabbit:**
- `YYYY-MM-DD` · log `.cursor/skills/coderabbit/.cache/cr-….jsonl` · N findings (C Critical, M Major, m Minor) → CURRENT.
```

   - **Формат сообщения — один `→`:** до `→` = снимок (дата · log · counts; **без** open/skipped/id); после `→` = текущее open C/H/M/L. Снимок не переписывать; правую часть синхронизировать на всех bullets при новом прогоне / смене open. Детали — skill [`coderabbit`](../coderabbit/SKILL.md).
   - Каждый последующий прогон — **новый** bullet `- …` (append; не удалять предыдущие).
   - Placeholder `- не запускался.` / `- —` заменять только первым реальным прогоном.

3. **PR** (вне blockquote): `**PR:** [#N]({{REPOSITORY_LINK}}/pull/N) (\`BREAKING:\` …).` — нет PR → `**PR:** —`.

**Когда открывать существующий `docs/RELEASE-PLAN-X.Y.Z.md` / `docs/TO-DO.md`:**
- **Обязательно (точечно):** перед любой **меняющей состояние** работой над ними — merge/open пунктов, close/dismiss, finalize, harvest leftovers, проверки renumber / dedupe. Всегда читать **текущий** план + `TO-DO.md` (только секции, которые правите).
- **Также допустимо (точечно, в том же ходе):** при harvest leftovers, дедупликации или проверке, закрыт ли уже пункт — читать open severity-секции **предыдущего** плана и только релевантные строки «Закрыто» (по id / смыслу). **Не** загружать полную историю всех version plan.
- **Опционально:** если **шаблон** неоднозначен/неясен (смысл секции, форма строки «Закрыто», …) — один точечный взгляд на version plan только за формой.
- **Исключение:** при любом проходе по релиз плану (черновик / обновление / finalize) — **Previous plans published/closed** (цепочка «Предыдущий план», только шапка).
- **Запрещено:** рутинно сканировать / перечитывать сгенерированные планы, когда нет смены состояния; считать сгенерированный план каноном skill или синхронизировать этот skill-файл с каждым выводом плана. **Не** `ls` / glob всех `docs/RELEASE-PLAN-*.md`, чтобы «найти предыдущие» — только цепочка ссылок **Предыдущий план**.

Downstream triage **coderabbit** по-прежнему пишет только в **текущий** version plan (не в `TO-DO.md` для delta findings) и пропускает дубликаты, уже открытые в текущем плане, любом плане «Закрыто» или `TO-DO.md`.

**Легенда:** ⬜ open · ✅ done · 🟨 partial / принято · ❌ blocker
**Критично / Высокий / Средний / Низкий** — только ⬜ **этой дельты**.
**Закрыто** — столбец `#`: **`✅ #M13 Short title`** / **`✅ #H3 …`** (legacy `✅ #34 …` ok). Без id: **`✅ Short title`**.

Пустые severity-секции оставлять как заголовок + `---`.

**Нумерация open items** — **общий** namespace с [`docs/TO-DO.md`](../../../docs/TO-DO.md) (не локальный счётчик релиза):

| Префикс | Секция |
|---|---|
| `C` | Критично |
| `H` | Высокий |
| `M` | Средний |
| `L` | Низкий |

**Источник max (allocate, без правки `TO-DO.md`):**
`max(Id high-water в шапке TO-DO, id в open + «Закрыто» текущего плана)` по группе → **+ 1**.
**`Id high-water` в `TO-DO.md` не трогать** до **finalize** этого релиза. Исторические id не перенумеровывать / не переиспользовать.

Источник finding’а **не хранить отдельной секцией** — сразу в C/H/M/L open **этого** плана (если относится к дельте) или в `TO-DO.md` (если вне дельты).

## `docs/TO-DO.md` (инкрементально)

Файл = **открытый** backlog **вне** дельты текущего version plan **плюс** кросс-версионная память принятых trade-off’ов.
Процесс/легенда/статусы **не** писать в сам файл — только здесь.

| Правило | Деталь |
|---|---|
| Содержимое | Open backlog вне дельты version plan; **Принято** — lasting contracts/trade-offs между релизами; планы = только дельта релиза |
| Секции | Четыре open: Критично / Высокий / Средний / Низкий (пустые = заголовок + `---`) **и** **Принято** (список bullets; может быть пустым) |
| Формат open | `### M13. Title` + описание **без** статус-маркеров (`⬜`/`✅`/…) |
| Формат Принято | bullet `- …` (без id / без ⬜✅ / **без версии** `2.x`/`v2.x`); дедуп по смыслу |
| Id | Общий namespace с version plan. Новый id = **max(TO-DO high-water, current plan open+«Закрыто» ids) + 1**. Не gap-fill / не переиспользовать |
| High-water | Строка **`Id high-water`** в шапке TO-DO = якорь **после последнего finalize**. **Писать только при finalize** (`max(старый HW, все id закрываемого релиза)`). Во время релиза high-water **не** обновлять |
| Источник | leftover plan / audit вне дельты / … — сразу в C/H/M/L |
| Harvest | Open с предыдущего плана, не вошедшее в дельту → добавить сюда (если ещё нет) |
| Close | См. **Close from TO-DO** — сначала «Закрыто» текущего плана, потом удалить из **open** C/H/M/L TO-DO (**Принято** не чистить при close open-пункта) |
| Принято sync | **Только при finalize.** Во время релиза lasting trade-off → **только** «Принято» текущего version plan. В `TO-DO.md` «Принято» — **запрещено** mid-release |
| Не класть | Work **этой** дельты в open C/H/M/L (оно в version plan); таблицу «Закрыто»; копипаст всего TO-DO в version plan (только ссылка) |

```markdown
## Критично (безопасность)
---
## Высокий (логика / licensing / auth model)
---
## Средний …
## Низкий …
---
## Принято (осознанный trade-off)

- …
```

## Previous plans `(published / closed)`

При проходе по релиз плану — проверять предыдущие на предмет выставления `(published / closed)`.

Каждый черновик / обновление / finalize version plan:

1. Идти по цепочке **Предыдущий план** от текущего (пока не `—` / нет файла). **Не** glob всех `docs/RELEASE-PLAN-*.md`.
2. Для каждого **уже finalized** плана: если метка шапки — `(closed)` (без `published`) **и** есть git tag и/или GitHub release `vX.Y.Z` — заменить только метку на **`(published / closed)`**. Тело / «Закрыто» / TO-DO не трогать.
3. Уже `(published / closed)` — пропуск. Нет tag/release — оставить `(closed)`.
4. **Текущий** план: `published / closed` только если tag/release `v{target}` уже есть; иначе при finalize — `(closed)`.

Проверка tag: `git rev-parse --verify vX.Y.Z^{commit}` и/или `gh release view vX.Y.Z`.

## Ensure current RELEASE-PLAN

Перед triage (CodeRabbit, issue/PR), close/dismiss, `docs/BREAKING.md`, или любой записью в version plan — **сначала** определить текущий план. См. **Cross-skill references** — ссылка одной строкой, без дублирования ниже.

```bash
bash .cursor/skills/release-plan/scripts/resolve-target-version.sh
bash .cursor/skills/release-plan/scripts/resolve-target-version.sh --json
```

Использовать `plan_path` / `target_version` из вывода (GitVersion `MajorMinorPatch`, либо `--version`). Exit **1** → починить GitVersion / теги, или передать `--version`.

| Ситуация | Действие |
|---|---|
| Текущий `docs/RELEASE-PLAN-X.Y.Z.md` **существует** | Использовать его (`test -f` / читать **только этот файл** + `docs/TO-DO.md` при необходимости); `plan_path` из вывода скрипта |
| **Нет** текущего плана для целевой версии (файл отсутствует) | **Обязательно** прогнать этот skill **полностью** (собрать delta → записать план) в этой же сессии, **затем** продолжить |
| Версия неизвестна | `resolve-target-version.sh` (GitVersion) или явный `--version X.Y.Z` |

**Запрещено:**
- `ls` / glob / read-all `docs/RELEASE-PLAN-*.md` (вкл. `to-master`), чтобы «найти текущий»
- изобретать stub-план без workflow этого skill; пропускать создание плана, когда его нет
- рутинно открывать исторические version plan (только текущий + TO-DO; ссылка на предыдущий план — при черновике шапки **нового** плана **и** при **Previous plans published/closed**)

**Правила версии** (скрипт зеркалит это; не копировать в другие skills):

`target_version` = **GitVersion** `MajorMinorPatch` на **текущей** ветке (`GitVersion.yml` + история). Любая ветка.

Ручной override: `--version X.Y.Z`. Скрипт: `dotnet-gitversion /nofetch /showvariable MajorMinorPatch` (`PATH` / `~/.dotnet/tools`; без `/nofetch` возможен hang на remote fetch). `from_version` — последний стабильный `vX.Y.Z` tag. Поля BREAKING: `breaking_from`, `breaking_to`.

**Текущий** `docs/RELEASE-PLAN-X.Y.Z.md` = план **целевой** версии (`target_version` / user / `**Версия:**` в файле). Писать закрытия только в **текущий** plan — не в shipped historical plans. Не использовать `RELEASE-PLAN-to-master.md`.

## `docs/BREAKING.md`

Breaking changes для потребителей. См. **Cross-skill references** — ссылка одной строкой + domain body (имена SQL, таблицы API, …).

### Phase 1 — Scaffold

1. **Ensure current RELEASE-PLAN** — `breaking_from` / `breaking_to` из скрипта.
2. Scaffold (только cache; **не** пишет в repo):

```bash
bash .cursor/skills/release-plan/scripts/scaffold-breaking-section.sh \
  --out .cursor/skills/release-plan/.cache/breaking-X.Y.Z.md
```

Опционально: `--pr N`, `--from`, `--to`, `--version`.

### Phase 2 — Правка `docs/BREAKING.md`

1. Вставить строку TOC + секцию **в начало** versioned-блоков (newest-first); заполнить `{{BODY}}`; префикс заголовка PR `BREAKING:`.
2. **Не** дублировать layout rules во intro `docs/BREAKING.md` — только текст для потребителей.

**Layout** ([`templates/BREAKING-SECTION.md`](templates/BREAKING-SECTION.md) — только сниппет):

- **Первый** блок после intro: intro заканчивается на `---` — без лишнего `---` перед заголовком.
- Между `---` и `## From …` — **пустая строка** (и для первого, и для последующих блоков).
- **Последующие** блоки: `---` перед секцией (после предыдущего тела), затем пустая строка, затем `## From …`.
- **После** `## From … to …` — пустая строка, затем `Release:` (или `###`, если нет `Release:`).
- **`Release:`** — `[vX.Y.Z](release-url)`; `([PR #N](…)).` когда PR известен. Без `(planned)`, без отсылок к project-specific docs — см. `README.md`.

При правке `docs/BREAKING.md` синхронизировать чеклист to-master, если меняются связанные пункты плана (DOC6, §10) — запустить `release-plan-to-master.mjs --write` (см. ниже).

## Close from TO-DO (обязательно, любой dismiss)

Когда пункт убирают из `docs/TO-DO.md` (fix, won’t-fix, dismiss, «это только пример», duplicate, …):

1. **Сначала** добавить строку в `## Закрыто` **текущего** `RELEASE-PLAN-X.Y.Z.md`:

| # | Суть |
|---|---|
| ✅ #H2 Scripts README MERGE SystemId scope | dismissed: README — пример lookup, не open work |

2. Id **сохранить** (`✅ #H2 …` / `✅ #M13 …`); title короткий; в «Суть» — почему закрыто.
3. **Затем** удалить пункт из **open** C/H/M/L в `docs/TO-DO.md` (пустые C/H/M/L-секции оставить; **Принято** не трогать).
4. Обновить **Приоритет** в TO-DO / плане при необходимости.
5. **Запрещено:** удалить из TO-DO open без строки в «Закрыто» текущего плана.

Осознанный **контрактный** lasting trade-off без id → **только** «Принято» текущего плана (**не** в `TO-DO.md` до finalize).
Id’шный backlog, который отклонили как trade-off → **Закрыто** с `✅ #Id …` **и** при lasting-контракте — bullet в **Принято** плана (**не** в `TO-DO.md` до finalize).

## Re-check (закрытие пунктов в version plan)

1. Закрываемый пункт **убрать** из severity-секций этого `RELEASE-PLAN-X.Y.Z.md` (если был open в дельте).
2. Добавить в `## Закрыто` (тот же формат `✅ #M13 …` / `✅ #H3 …`).
3. Id **сохранить**; title короткий.
4. Обновить **Приоритет фиксов** плана (только work этой дельты).
5. **Удалить** тот же пункт из **open** C/H/M/L `docs/TO-DO.md`, если он там был (после шага 2; секцию **Принято** в `TO-DO.md` **не** трогать).
6. То же правило, что **Close from TO-DO**: нельзя только выкинуть из TO-DO.

## Finalize version plan (закрытие релиза)

Когда пользователь просит **закрыть / финализировать / ship** `docs/RELEASE-PLAN-X.Y.Z.md` (релиз вышел или план этой версии больше не ведётся):

1. **Собрать весь ⬜ open** из секций Критично / Высокий / Средний / Низкий этого плана.
2. **Перенести** каждый пункт в [`docs/TO-DO.md`](../../../docs/TO-DO.md) (merge **по id** — один id = одна задача; формат TO-DO **без** `⬜`; open-секции C/H/M/L сохранить; **Принято** TO-DO не затирать).
   Не класть их в «Закрыто» — это не done/dismiss, а leftover.
3. **Синхронизировать «Принято»** этого плана → «Принято» `TO-DO.md` (merge/dedupe **по смыслу**; **единственный** момент записи lasting trade-off’ов релиза в TO-DO).
4. **Обновить `Id high-water`** в шапке `TO-DO.md` (**единственный** момент записи HW в этом релизе): для каждой группы `max(текущий high-water, все id релиза)` — leftovers + строки «Закрыто» вида `✅ #H9 …` / `✅ #M49 …` / ….
5. **Привести план к завершённому шаблону** [`templates/RELEASE-PLAN-FINALIZED.md`](templates/RELEASE-PLAN-FINALIZED.md):
   - header: **`(published / closed)`**, если есть git tag / GitHub release `vX.Y.Z`; иначе **`(closed)`** (`CLOSED_LABEL` в [`FINALIZE-REPLY`](templates/FINALIZE-REPLY.md));
   - C/H/M/L — **пустые** (только заголовок + `---`);
   - **Принято** / **Закрыто** / **Что в библиотеке уже нормально** — сохранить содержимое этого релиза;
   - **Приоритет фиксов** — пустая отсылка к `TO-DO.md` (как в finalized template).
6. **Previous plans published/closed** — см. выше (цепочка «Предыдущий план»).
7. Обновить **Приоритет** в `TO-DO.md` при необходимости (новые leftovers).
8. UTF-8 BOM на изменённых docs.
9. **Ответ пользователю** — по [`templates/FINALIZE-REPLY.md`](templates/FINALIZE-REPLY.md).

**Запрещено:** оставить ⬜ open в «закрытом» плане; удалить open без переноса в TO-DO; glob / read-all historical plans (кроме цепочки **Previous plans published/closed**).

## Workflow

### Phase 1 — Resolve & collect

1. **Ensure current RELEASE-PLAN** — см. выше; base по умолчанию `origin/master`.
2. **Собрать delta** (обязательно) — только скрипт; **не** класть путь cache в файл version plan:

```bash
bash .cursor/skills/release-plan/scripts/collect-release-delta.sh \
  --base origin/master \
  --version X.Y.Z
```

По умолчанию в cache попадает diff `docs/BREAKING.md`. Дополнительные «горячие» пути — из `README` / `name-status`, repeatable `--focus PATH` (без hardcode layout в скрипте). Отключить default: `--no-default-focus`. Опционально: `--version X.Y.Z`.

```bash
bash .cursor/skills/release-plan/scripts/collect-release-delta.sh \
  --base origin/master \
  --version X.Y.Z \
  --focus '<library-or-src-path>/' \
  --focus '<tests-path>/'
```

Cache попадает под `.cursor/skills/release-plan/.cache/` (скрипт печатает путь). Использовать при черновике; не включать в `docs/RELEASE-PLAN-X.Y.Z.md`.

### Phase 2 — Черновик плана

1. **Синхронизировать `TO-DO.md`** — harvest leftovers в C/H/M/L; убрать пункты, закрытые в этой дельте / любом version «Закрыто».
2. **Записать** `docs/RELEASE-PLAN-X.Y.Z.md` по шаблону — **только delta** (UTF-8 **with BOM**).
3. **Previous plans published/closed** — см. выше.
4. Классифицировать изменения **дельты**:

| Корзина | Куда класть |
|---|---|
| Критично / Высокий / Средний / Низкий | Open issues **только в этой дельте** |
| Принято | Trade-offs **этого** релиза — **только** в version plan; в `TO-DO.md` «Принято» — **только при finalize** |
| Закрыто | Fixes/features **в этой дельте** |
| Что в библиотеке уже нормально | Краткие bullets **про инварианты этой дельты** |
| Приоритет фиксов | Оставшаяся работа **только этого релиза** (+ ссылка на `TO-DO.md`) |

### Phase 3 — Документы для потребителей

1. **`docs/CHANGELOG.md`** — **всегда** при черновике / обновлении version plan и перед publish (секция `## vX.Y.Z` newest-first, English). Только скрипт — не писать секцию вручную, если скрипт можно запустить:

```bash
node .cursor/skills/release-plan/scripts/update-changelog.mjs --write
# optional: --version X.Y.Z --from A.B.C --dry-run
```

После `--write`: если path-bullets слишком грубые — **точечно** уточнить bullets в той же секции (не дублировать заголовок, не ломать newest-first / UTF-8 BOM). Open-пункт «нет секции CHANGELOG» закрывать в «Закрыто» текущего плана.

2. **`docs/BREAKING.md`** — если в этой дельте есть breaking для потребителей: см. **`docs/BREAKING.md`** выше.
3. **Language:** тело version plan на русском; CHANGELOG — **English**; в таблице «Суть» допустима смесь RU/EN имён.

## Прочие release-документы (не version plans)

| Файл | Роль |
|---|---|
| `RELEASE-PLAN.md` (корень репо) | Аудит библиотеки / hardening backlog |
| `docs/RELEASE-PLAN-to-master.md` | Исторические readiness-чеклисты → `master` |
| `docs/BREAKING.md` | Breaking changes для NuGet-потребителей |

Version plans (`docs/RELEASE-PLAN-X.Y.Z.md`) и `docs/TO-DO.md` — см. выше. **Не** подменять чеклист to-master version plan’ом.

### Статус-метки корневого `RELEASE-PLAN.md`

**Легенда:** ⬜ open · ✅ done · 🟨 partial / accepted · ❌ blocker

При закрытии пункта (fixed или accepted):

1. Префиксовать заголовок зелёным чекбоксом `✅` (напр. `### ✅ 22. …`) — **не** использовать один лишь текст «закрыто».
2. Добавить/обновить строку в **Закрыто** с `✅ #N …`.
3. Убрать пункт из открытых списков **Приоритет фиксов**.

### `docs/RELEASE-PLAN-to-master.md` — Change summary

**Maintainer / agent only** (не контрибьюторский чеклист; не в PR template). Skill `release-plan` ведёт файл; скрипт лишь синхронизирует строку **Change summary**.

**При любом изменении** `docs/RELEASE-PLAN-to-master.md` (статусы ⬜/✅/🟨/❌, новые пункты, §8 DB migration, DOC6, breaking changes, release gate, go/no-go) **всегда** пересчитывать и обновлять строку **"Change summary"** в шапке документа (сразу после легенды).

То же при правке `docs/BREAKING.md`, если меняется статус связанных пунктов плана (напр. DOC6, §10.8, P1 для `collectResult`).

```bash
node .cursor/skills/release-plan/scripts/release-plan-to-master.mjs --write
```

Без `--write` — только вывести строку для проверки. Не править проценты и счётчики вручную, если скрипт можно запустить.

**Легенда статусов:** ⬜ open · ✅ done · 🟨 partial · ❌ blocker

### Breaking changes ↔ план to-master

| Область | Где в плане to-master |
|---|---|
| `docs/BREAKING.md` | §2 `B1`–`B4`, go/no-go `G2` |
| `config.nuspec` releaseNotes | §2 `B3`, §4 `N1` (version-plan L#) |
| Version plan / TO-DO | §1 `P2`–`P3`, §5 `A3` |

Workflow новых секций: **`docs/BREAKING.md`** (этот skill).

## Скрипты (`scripts/`)

| Скрипт | Назначение |
|---|---|
| [`resolve-target-version.sh`](scripts/resolve-target-version.sh) | `target_version` = GitVersion `MajorMinorPatch` (или `--version`); `plan_path`, `repository_link`, `breaking_from`/`breaking_to` |
| [`scaffold-breaking-section.sh`](scripts/scaffold-breaking-section.sh) | Строка TOC + блок `From X to Y` (только cache; агент правит `docs/BREAKING.md`) |
| [`collect-release-delta.sh`](scripts/collect-release-delta.sh) | Cache delta ветки для черновика плана; default focus `docs/BREAKING.md`; `--focus PATH` (repeatable) |
| [`update-changelog.mjs`](scripts/update-changelog.mjs) | Upsert `docs/CHANGELOG.md` § `vX.Y.Z` из delta (`v{from}..HEAD` + WT); `--write` / `--dry-run` |
| [`release-plan-to-master.mjs`](scripts/release-plan-to-master.mjs) | Строка Change summary в `RELEASE-PLAN-to-master.md` |

Другие skills: **Cross-skill references** (ссылка одной строкой; без дублирования скриптов или prose про layout).

## Локальный `dotnet test`

Если в test `.csproj` есть свойство `SkipNetCoreApp31Tests` — к `dotnet test` добавлять `-p:SkipNetCoreApp31Tests=true` (без x64 3.1 host VSTest зависает на Darwin Arm64). Иначе не добавлять.

Целевой csproj: из PR template / discovery (`**/*Tests*.csproj`), **не** хардкодить имя продукта.

```bash
dotnet test <TestProject>/<TestProject>.csproj -p:SkipNetCoreApp31Tests=true
```

## Quality bar

- [ ] Version plan **без** backlog чужих релизов (он живёт в `TO-DO.md`)
- [ ] Version plan **без** ссылок на более новый SemVer / более новый `RELEASE-PLAN-*`
- [ ] `TO-DO.md` — open C/H/M/L + **Принято** (без «Закрыто» / без review-tool секции); закрытые open-пункты из C/H/M/L удалены
- [ ] Каждое удаление из open `TO-DO.md` имеет парную строку `✅ #Id …` в «Закрыто» **текущего** плана
- [ ] Во время открытого релиза lasting trade-off’ы **только** в «Принято» version plan — **не** в `TO-DO.md`
- [ ] «Закрыто» `#` вида `✅ #M13 …` / `✅ #H3 …` (или legacy `✅ #34 …`)
- [ ] Каждая строка «Закрыто» опирается на evidence дельты **или** явную причину dismiss
- [ ] Finalize выполнен по секции **Finalize version plan** (план → [`RELEASE-PLAN-FINALIZED`](templates/RELEASE-PLAN-FINALIZED.md); ответ → [`FINALIZE-REPLY`](templates/FINALIZE-REPLY.md))
- [ ] Новые id C/H/M/L = max(TO-DO HW, current plan ids) + 1; **без** mid-release правок HW в `TO-DO.md`
- [ ] UTF-8 BOM на записанных plan / TO-DO, если новые
- [ ] Новые секции `BREAKING.md` следуют [`templates/BREAKING-SECTION.md`](templates/BREAKING-SECTION.md) (layout не дублируется во intro для потребителей)
- [ ] `docs/CHANGELOG.md` имеет секцию целевой версии (`update-changelog.mjs --write`); UTF-8 BOM сохранён
- [ ] Предыдущие finalized-планы с существующим tag/release `vX.Y.Z` имеют в шапке `(published / closed)` (цепочка **Предыдущий план**, не glob)
