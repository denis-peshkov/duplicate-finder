---
name: coderabbit
description: >-
  Runs CodeRabbit CLI review of the current branch vs master (committed delta),
  saves agent findings, and always merges Critical/Major/Minor/Trivial/Info into
  the current docs/RELEASE-PLAN-X.Y.Z.md as open C/H/M/L (not into docs/TO-DO.md).
  If no current version plan exists, runs the release-plan skill first to create
  it, then merges findings. Closing/dismissing a plan item moves it to that
  plan’s «Закрыто» as `✅ #Id …`. Use when the user asks to run CodeRabbit, CR
  review, or local coderabbit on branch changes — and whenever the user pastes
  or quotes a CodeRabbit finding / agent review (incl. «объясни», footer nudge
  «After applying the fix…», docs.coderabbit.ai/cli, utm_source=ghpr): read this
  skill immediately; Phase 3 open C/H/M/L in the SAME turn as any explanation —
  never explain-only without a plan row; fix = Phase 4 same turn (no silent code-only).
---

# CodeRabbit vs master

## When to use

- User asks to run **CodeRabbit** / **CR** / `coderabbit` on the current branch
- Local review of committed changes vs `master` before a PR / release plan
- User pastes / quotes a CR finding or agent review — including **only** «объясни» /
  explain / «что это» — **or** the footer nudge
  (`After applying the fix, consider running \`coderabbit review --agent\``,
  `docs.coderabbit.ai/cli`, `utm_source=ghpr`) — **read this skill immediately**
- **Same turn:** Phase **3** (open C/H/M/L in RELEASE-PLAN) **before or with** any
  explanation; Phase **4** when fixing. **Forbidden:** explain-only / chat-only
  without writing the finding into the current plan

## Defaults

| Flag | Value |
|---|---|
| Base | `origin/master` (fallback `master`) |
| Scope | committed branch delta (`--committed`) |
| Output | `--agent` (JSONL findings for agents) |
| After review | **always** triage into the **current** [`docs/RELEASE-PLAN-X.Y.Z.md`](../../../docs/) (not `TO-DO.md`) |
| No plan | Skill [`release-plan`](../release-plan/SKILL.md) → **Ensure current RELEASE-PLAN** · full workflow if the plan is missing |
| CLI | `coderabbit` from `PATH` (also `~/.local/bin`) |

## GitHub PR bot (not the local CLI)

Local `coderabbit review` ≠ the GitHub bot. To re-run on a PR after auto-pause (see `.coderabbit.yaml` → `auto_pause_after_reviewed_commits`), leave a comment on the PR:

```text
@coderabbitai full review
```

| Command | Effect |
|---|---|
| `@coderabbitai full review` | full review of the entire PR from scratch |
| `@coderabbitai review` | only new changes since the last review |

Ack: `Full review triggered` → `Full review finished`. Docs: [Review commands](https://docs.coderabbit.ai/reference/review-commands).

Optional: `coderabbit pullrequest <n> --agent` reads an existing GitHub review into the agent (does not start a new bot run).

## Workflow

### Phase 1 — Prerequisites

1. Skill [`release-plan`](../release-plan/SKILL.md) → **Ensure current RELEASE-PLAN** · CR findings → plan, not TO-DO (before or after review, before Phase 3).
2. **Auth / doctor** (if review fails):

```bash
export PATH="$HOME/.local/bin:$PATH"
coderabbit auth status
coderabbit doctor
```

If not logged in: tell the user to run `coderabbit auth login` in their own terminal (browser OAuth). Do not invent findings.

### Phase 2 — Review

1. **Run the review** (required — Shell with unrestricted permissions so `~/.coderabbit` storage works):

```bash
bash .cursor/skills/coderabbit/scripts/run-coderabbit-review.sh \
  --base origin/master
```

Optional:

```bash
# Narrow scope (Free plan ~150 files). Pick <path> from the delta, e.g.:
#   git diff --name-only origin/master...HEAD | awk -F/ 'NF{print $1}' | sort -u
bash .cursor/skills/coderabbit/scripts/run-coderabbit-review.sh \
  --base origin/master --dir <path>

# Lighter / include uncommitted
bash .cursor/skills/coderabbit/scripts/run-coderabbit-review.sh \
  --base origin/master --light --uncommitted
```

The script prints the log path under `.cursor/skills/coderabbit/.cache/`.

2. **Summarize** findings from the log / `coderabbit review findings`:
   - Count by severity
   - Table: severity · file · short gist
   - **Do not** invent issues that are not in the output

Order: Phase **1** step **1** may run before Phase **2** (plan first) or after Phase **2** step **2** (create the plan after the summary, before Phase 3). Review and plan creation may run sequentially; **Phase 3 only after the plan file exists**.

### Phase 3 — Sync with RELEASE-PLAN

**Always — not optional.** Applies after CLI review **and** when the user pastes a
finding (even if they only ask «объясни»). Target = the current plan from Phase **1**
step **1** (created via `release-plan` if it was missing).

**Order for pasted findings:**
1. Verify against current code (still-valid? skip with reason if not). Skip-list (ниже) — **не** писать open C/H/M/L.
2. **Write** open `### L…` / `### M…` / … into the plan (**Phase 3**) — **before** or
   in the same edit burst as the chat explanation.
3. Then explain in chat (may cite `#Id`).
4. Code fix only on «фикси» / fix → **Phase 4** (close same id).

**Forbidden:** reply that only explains a pasted CR finding and leaves
`docs/RELEASE-PLAN-X.Y.Z.md` unchanged.

Immediately merge findings into that plan’s open severity sections **only as C/H/M/L** (no separate CR section).
**Do not** write CR findings into [`docs/TO-DO.md`](../../../docs/TO-DO.md).

**Also update the plan header** (Skill [`release-plan`](../release-plan/SKILL.md) → шапка / хвост):

```markdown
**CodeRabbit:**
- `YYYY-MM-DD` · log `.cursor/skills/coderabbit/.cache/cr-….jsonl` · N findings (C Critical, M Major, m Minor) → CURRENT.
```

- Date = review day; log = path printed by `run-coderabbit-review.sh`.
- Counts from **this** run (Critical/Major/Minor; Trivial/Info fold into Minor count **or** note separately if non-zero).
- **Формат сообщения — один `→`:**
  - **До `→` (снимок прогона, не переписывать):** только дата · log(s) · dirs (если split) · `N findings (C Critical, M Major, m Minor)`. **Без** «открыты в плане», skipped, id — это в чат / C/H/M/L, не в bullet.
  - **После `→` (текущее):** `все закрыты в этом плане.` / `Open: Cx Hy Mz Lw` / `K открыты (#…)`. При каждом новом прогоне (и если в том же ходе Phase 3/4 меняет open) — **обновить текст после `→` у всех** bullets.
- **Append, never overwrite:** один заголовок `**CodeRabbit:**`; каждый прогон = **новый** bullet `- …` сразу после последнего bullet (перед `**PR:**`). **Не** удалять предыдущие bullets и **не** менять их снимок (текст до `→`).
- Placeholder `- не запускался.` / `- —` — **только при первом** реальном прогоне заменить на первый dated bullet; дальше только append.
- Один логический прогон с несколькими `--dir` (один день / одна сессия) = **один** bullet (logs glob + dirs), как раньше.
- Keep **`**PR:**`** line as-is unless the user/PR context changed.
- Refresh the blockquote **Дельта:** line (`{{BASE}}...HEAD` counts + `Open C/H/M/L …`) when open C/H/M/L change in the same turn.

| CodeRabbit | Plan section |
|---|---|
| Critical | `## Критично` → `C…` |
| Major | `## Высокий` → `H…` |
| Minor | `## Средний` → `M…` |
| Trivial / Info | `## Низкий` → `L…` |

Format (as in the plan legend): `### M43. Title` + `⬜` description.

Rules:
- Merge by meaning; next id = **max(`Id high-water` in TO-DO, open+«Закрыто» ids of the current plan) + 1** per group (`C`/`H`/`M`/`L`). **Do not** bump high-water in `TO-DO.md` until **Finalize version plan** ([`release-plan`](../release-plan/SKILL.md))
- Skip duplicates already open in the current plan or already in any plan’s «Закрыто»
- Skip duplicates already open in `TO-DO.md` (same meaning) — **do not** copy them into the plan’s open C/H/M/L, **do not** include them in **Приоритет фиксов**, **do not** count them as release work unless the user asks
- **Не заносить** в version plan finding, что `docs/CHANGELOG.md` § `## vX.Y.Z` «выглядит published» (дата в заголовке, нет `Unreleased`) до git tag / GitHub Release. Канон: notes целевой версии писать как dated `vX.Y.Z` **до** tag; **не** предлагать `Unreleased` / pending. В чате: `skipped (CHANGELOG dated-by-design)`
- In the chat reply: a short note like “skipped (already in TO-DO: H1, M44)” is enough; no plan edits for those
- Leave empty severity sections as heading + `---`; UTF-8 BOM
- Update **Приоритет фиксов** of the current plan only for **newly opened** items added to this plan
- In the chat reply: list what was **added** / **skipped** (and note if `release-plan` was run to create the file)

### Phase 4 — Close / dismiss / fix (same turn — never code-only)

**This skill owns quiet-fix prevention for CR findings** — not `release-plan`.  
When the user closes, rejects, dismisses, **or asks to fix** («фикси», «fix», pasted CR finding / `utm_source=ghpr`):

1. Skill [`release-plan`](../release-plan/SKILL.md) → **Ensure current RELEASE-PLAN** / **Re-check** (plan file + id rules only).
2. **First** allocate/reuse id (open ⬜ optional if fixed immediately).
3. Apply the code fix **only together with** `| ✅ #Id Short title | … |` under `## Закрыто` of this plan (id prefix by severity: Minor→`#M…`, Trivial/Info→`#L…`).
4. **Then** remove the item from the open severity section (if it was open).
5. If the same id somehow still exists in `docs/TO-DO.md` — remove it there too — Skill [`release-plan`](../release-plan/SKILL.md) → **Close from TO-DO** / **Re-check**.
6. **Never** drop an open item without a «Закрыто» row.
7. **Never** end the turn with code/CI/docs changes and an untouched plan («тихий фикс»).
8. **Fix-in-same-turn:**
   - Finding **already open** in the current plan (`### M52. …` ⬜ / same meaning) → move to «Закрыто» as `✅ #M52 …` with the **same `#Id`**; **do not** allocate a replacement id.
   - Finding **not yet** in the current plan (new in this turn) → allocate the next `C/H/M/L` id via max(TO-DO HW, current plan open+«Закрыто» ids)+1 (no mid-release HW write), then write `✅ #M59 …` (etc.) under «Закрыто» (open ⬜ row optional if fixed immediately).
   - Always keep the severity prefix; **do not** skip the «Закрыто» row.
   - Chat reply must name the `✅ #Id` closed.

## Limits

- Free plan often caps **~150 files** per review. If the branch delta is larger: narrow with `--dir <path>` (path from the delta; split into several runs by top-level areas) or use `--light`.
- Review may take several minutes — use a high Shell `block_until_ms` (e.g. 600000).

## Quality bar

- [ ] Used `--committed --base` vs master (or the base the user specified)
- [ ] Ran outside sandbox restrictions that break `~/.coderabbit`
- [ ] Summary matches the saved log
- [ ] **Did not** glob/`ls` all `docs/RELEASE-PLAN-*.md`; only the current plan (+ TO-DO when needed)
- [ ] If no current plan existed → skill `release-plan` ran and created `docs/RELEASE-PLAN-X.Y.Z.md` before triage
- [ ] **Current** `docs/RELEASE-PLAN-X.Y.Z.md` updated in the same turn (open C/H/M/L); **not** `TO-DO.md` for CR findings
- [ ] Header `**CodeRabbit:**` — **appended** new `-` bullet; previous kept; до `→` только дата/log/counts (без open/skipped ids); после `→` CURRENT synced on all bullets
- [ ] **Did not** open a C/H/M/L row for CHANGELOG «looks published before tag» (dated `## vX.Y.Z` is by design)
- [ ] Pasted finding + «объясни» → open C/H/M/L row written **before/with** the explanation (not explain-only)
- [ ] Any dismissed/closed/**fixed** item → `✅ #Id …` in this plan’s «Закрыто» **in the same turn as the code change** (no quiet fixes)
- [ ] Any dismissed/closed item → `✅ #Id …` in this plan’s «Закрыто» before removal from open sections
