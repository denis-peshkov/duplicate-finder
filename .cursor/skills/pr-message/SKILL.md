---
name: pr-message
description: >-
  Drafts GitHub PR title + body from .github/PULL_REQUEST_TEMPLATE.md for the
  current branch (or named branch) vs base. Auto-checks verifiable Test plan /
  Checklist boxes after local build/test and diff heuristics. Use when the user
  asks for a PR message, PR body, «месадж ПР», «сообщение ПР», «текст PR»,
  «draft PR description», or to fill the pull request template — without
  creating the PR unless they explicitly ask.
---

# PR message (template)

## When to use

- «месадж ПР» / «сообщение ПР» / «текст PR» / «PR message» / «draft PR body»
- Заполнить шаблон PR **без** `gh pr create`, пока пользователь явно не попросил создать PR

## Defaults

| Item | Value |
|---|---|
| Template | [`.github/PULL_REQUEST_TEMPLATE.md`](../../../.github/PULL_REQUEST_TEMPLATE.md) |
| Base | `origin/dev` for `feature/*` `fix/*` `chore/*`; `origin/master` for `release/*` `hotfix/*` (override if user names base) |
| Head | current branch, or `branch <name>` if given |
| Language | English (GitHub-facing) |
| Output | title + full body in one markdown block; do **not** open the PR unless asked |
| Shell | least privilege: default sandbox; elevate only when needed (`network` / `full_network` / `git_write` / `all`), smallest scope |

## Workflow

### Phase 1 — Context

1. Read `.github/PULL_REQUEST_TEMPLATE.md` (source of truth for section order and wording).
2. Resolve `BASE` / `HEAD`. Local `git` read/diff — sandbox. `git fetch` / `gh` — request `network` or `full_network` (smallest that works); do **not** use `all` unless those fail for a concrete sandbox reason:

```bash
git rev-parse --abbrev-ref HEAD
git fetch origin 2>/dev/null || true
git log --oneline "$BASE..$HEAD" | head -40
git diff --stat "$BASE...$HEAD"
git diff --name-status "$BASE...$HEAD"
git diff --shortstat "$BASE...$HEAD"
```

3. Optional: `gh pr list --head "$HEAD" --json number,url,baseRefName` — if a PR already exists, say so and still draft/update the body text (`network` / `full_network` as needed).
4. Skim delta hotspots (library / src API, tests, sample host, docs/BREAKING, LICENSE/secrets).
5. Resolve build/test targets for Phase 3 (**repo-agnostic**):
   - Prefer commands already written in the template Test plan (`dotnet build …` / `dotnet test …`).
   - Else discover: root `*.slnx` or `*.sln` (prefer `.slnx`); primary test project `**/*Tests*.csproj` / `**/*Test*.csproj` nearest the library (not under `node_modules`).
   - Do **not** hardcode a product name (solution / test csproj) in this skill.

### Phase 2 — Draft body

Fill **every** template section. Keep HTML comments out of the user-facing draft (or leave only if the template requires them — prefer clean filled sections).

| Section | How to fill |
|---|---|
| **Title** | Imperative summary; prefix `BREAKING:` only if consumer-breaking (and `docs/BREAKING.md` updated) |
| **Summary** | What changed and why (short narrative). `Closes: #N` or `Closes: —` |
| **Changes** | Numbered list: `` `path` — … ``; end with `**Scope:** N files, ~+X / −Y lines.` from `git diff --shortstat` |
| **Test plan** | Keep the three template bullets; mark `[x]` / `[ ]` per Phase 3 |
| **Risks / notes** | Required if licensing, DI registration, transactions, or breaking; else `N/A` |
| **Checklist** | Keep all template bullets; mark `[x]` / `[ ]` per Phase 3 |
| **AI assistance** | `[x]` + one line what AI did / what was verified, when this skill ran in an agent session; else `[ ]` |
| **License** | Keep the template license footer verbatim |

**No release version in PR message:** не писать SemVer / `vX.Y.Z` / «ship N.N.N» в title и body (версия — в tag / CHANGELOG / release plan). Исключение: путь к уже versioned-файлу.

### Phase 3 — Auto-check (only when verifiable)

Run checks that are cheap and conclusive. **Do not** mark a box unless evidence exists in this turn. On failure/skip → leave `[ ]` and note why under Risks or after the draft.

**Shell:** `dotnet build` / `dotnet test` — **sandbox** (no elevated permissions). Secret-scan / local `git diff` — sandbox. Elevate only for commands that need it (`gh`, `git fetch` → `network` / `full_network`; git writes → `git_write`). Use `all` only after a smaller scope fails for a documented sandbox reason.

#### Test plan

| Box | Auto `[x]` when |
|---|---|
| New or updated tests cover the changed behavior | Diff touches `**/*Tests*` / `**/*Test*` with meaningful test changes **or** production change is docs/rules-only (then still `[x]` only if no behavior change — otherwise leave `[ ]` if prod code changed without tests) |
| Template `dotnet build …` — green locally | Command from template (or discovered solution) succeeds in this turn |
| Template `dotnet test …` — green locally | Command from template (or discovered test csproj) succeeds in this turn (prefer all TFMs; at least one TFM if time-constrained — note partial) |

Preferred commands (sandbox). Keep the **exact** build/test lines from the PR template when present. Skill [`release-plan`](../release-plan/SKILL.md) → **Локальный `dotnet test`**.

```bash
# Examples only — replace with targets from the template / discovery:
dotnet build <solution.slnx|sln>
dotnet test <TestProject>/<TestProject>.csproj
```

#### Checklist

| Box | Auto `[x]` when |
|---|---|
| Read CONTRIBUTING | Always leave `[ ]` (human attestation) unless user says they read it **or** authored `CONTRIBUTING.md` |
| No other open PR for same fix/feature | `gh pr list --state open` shows no overlapping head/title/topic; if `gh` unavailable → `[ ]` |
| One PR = one feature/fix | Leave `[ ]` unless delta is clearly single-purpose (then `[x]`) |
| `.editorconfig` / no secrets | Spot-check diff: no live JWT/`eyJ…` license blobs, passwords, API keys; BOM/editorconfig not violated in touched files → `[x]`; on suspicion → `[ ]` + Risks note |
| Public API / README / XML | No public API/registration change → `[x]`; if changed and README/XML/docs updated in delta → `[x]`; if changed without docs → `[ ]` |
| Breaking → BREAKING.md + title | Not breaking → `[x]`; breaking and `docs/BREAKING.md` + `BREAKING:` title handled → `[x]`; else `[ ]` |
| Licensing/transactions risks + no secrets | Does not touch licensing/transactions → `[x]`; touches them and Risks filled + no secrets in diff → `[x]`; else `[ ]` |

#### AI assistance

- Agent-authored draft in this session → `[x]` + brief note (build/test/diff checks performed).
- User wrote the body alone → `[ ]`.

### Phase 4 — Reply

1. **Title** — alone in a fenced markdown code block (copy-paste ready), same as body:

````markdown
```text
BREAKING: rename public API surface for consumers
```
````

2. **Body** — full template in one fenced markdown code block (copy-paste ready).
3. One short line: base←head, which boxes were auto-checked, which left unchecked (and blockers if build/test failed).
4. **Do not** `gh pr create` / push unless the user explicitly asks.

Do **not** put the title only as plain prose outside a fence — both title and body must be easy to select/copy.

## Quality bar

- [ ] Body follows `.github/PULL_REQUEST_TEMPLATE.md` section order
- [ ] English only in title/body
- [ ] Scope numbers match `git diff --shortstat`
- [ ] No `[x]` without evidence from this turn
- [ ] Did not create the GitHub PR unless asked
- [ ] Title and body each in their own copy-paste fenced block
- [ ] Shell least privilege: sandbox for `dotnet build` / `dotnet test` and local reads; elevated only when required, smallest scope
