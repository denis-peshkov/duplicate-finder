---
name: pr-message
description: >-
  Drafts GitHub PR title + body from .github/PULL_REQUEST_TEMPLATE.md for the
  current branch (or named branch) vs base. Auto-checks verifiable Test plan /
  Checklist boxes after local pytest and diff heuristics. Use when the user
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
4. Skim delta hotspots (`src/`, `tests/`, `distribution/`, `.github/`, `docs/`, secrets).
5. Resolve test targets for Phase 3:
   - Prefer commands already written in the template Test plan (`pytest`).
   - Else: `pytest` from repo root after `pip install -e ".[dev]"` if needed.
   - Do **not** assume .NET / `dotnet build` / `*.csproj` in this repository.

### Phase 2 — Draft body

Fill **every** template section. Keep HTML comments out of the user-facing draft (or leave only if the template requires them — prefer clean filled sections).

| Section | How to fill |
|---|---|
| **Title** | Imperative summary; prefix `BREAKING:` only if user-breaking (and `docs/BREAKING.md` updated when present) |
| **Summary** | What changed and why (short narrative). `Closes: #N` or `Closes: —` |
| **Changes** | Numbered list: `` `path` — … ``; end with `**Scope:** N files, ~+X / −Y lines.` from `git diff --shortstat` |
| **Test plan** | Keep the template bullets; mark `[x]` / `[ ]` per Phase 3 |
| **Risks / notes** | Required if delete/Recycle Bin, packaging, or breaking; else `N/A` |
| **Checklist** | Keep all template bullets; mark `[x]` / `[ ]` per Phase 3 |
| **AI assistance** | `[x]` + one line what AI did / what was verified, when this skill ran in an agent session; else `[ ]` |
| **License** | Keep the template license footer verbatim (MIT) |

**No release version in PR message:** не писать SemVer / `vX.Y.Z` / «ship N.N.N» в title и body (версия — в tag / release). Исключение: путь к уже versioned-файлу.

### Phase 3 — Auto-check (only when verifiable)

Run checks that are cheap and conclusive. **Do not** mark a box unless evidence exists in this turn. On failure/skip → leave `[ ]` and note why under Risks or after the draft.

**Shell:** `pytest` — **sandbox** (no elevated permissions). Secret-scan / local `git diff` — sandbox. Elevate only for commands that need it (`gh`, `git fetch` → `network` / `full_network`; git writes → `git_write`). Use `all` only after a smaller scope fails for a documented sandbox reason.

#### Test plan

| Box | Auto `[x]` when |
|---|---|
| New or updated tests cover the changed behavior | Diff touches `tests/**` with meaningful test changes **or** production change is docs/rules-only (then still `[x]` only if no behavior change — otherwise leave `[ ]` if prod code changed without tests) |
| Template `pytest` — green locally | `pytest` succeeds in this turn |
| Manual UI check | Leave `[ ]` unless user confirms UI was checked (or PR has no UI changes → `[x]`) |

Preferred commands (sandbox). Keep the **exact** test lines from the PR template when present.

```bash
pytest
```

#### Checklist

| Box | Auto `[x]` when |
|---|---|
| Read CONTRIBUTING | Always leave `[ ]` (human attestation) unless user says they read it **or** authored `CONTRIBUTING.md` |
| No other open PR for same fix/feature | `gh pr list --state open` shows no overlapping head/title/topic; if `gh` unavailable → `[ ]` |
| One PR = one feature/fix | Leave `[ ]` unless delta is clearly single-purpose (then `[x]`) |
| `.editorconfig` / Python style / no secrets | Spot-check diff: no passwords, API keys, private paths; style not wildly violated → `[x]`; on suspicion → `[ ]` + Risks note |
| User-facing / docs | No user-facing change → `[x]`; if changed and README/`docs/` updated in delta → `[x]`; if changed without docs → `[ ]` |
| Breaking → BREAKING.md + title | Not breaking → `[x]`; breaking and `BREAKING:` title (+ `docs/BREAKING.md` when present) handled → `[x]`; else `[ ]` |
| Delete/packaging risks + no secrets | Does not touch delete/packaging → `[x]`; touches them and Risks filled + no secrets in diff → `[x]`; else `[ ]` |

#### AI assistance

- Agent-authored draft in this session → `[x]` + brief note (pytest/diff checks performed).
- User wrote the body alone → `[ ]`.

### Phase 4 — Reply

1. **Title** — alone in a fenced markdown code block (copy-paste ready), same as body:

````markdown
```text
BREAKING: rename settings keys for include masks
```
````

2. **Body** — full template in one fenced markdown code block (copy-paste ready).
3. One short line: base←head, which boxes were auto-checked, which left unchecked (and blockers if pytest failed).
4. **Do not** `gh pr create` / push unless the user explicitly asks.

Do **not** put the title only as plain prose outside a fence — both title and body must be easy to select/copy.

## Quality bar

- [ ] Body follows `.github/PULL_REQUEST_TEMPLATE.md` section order
- [ ] English only in title/body
- [ ] Scope numbers match `git diff --shortstat`
- [ ] No `[x]` without evidence from this turn
- [ ] Did not create the GitHub PR unless asked
- [ ] Title and body each in their own copy-paste fenced block
- [ ] Shell least privilege: sandbox for `pytest` and local reads; elevated only when required, smallest scope
