# Contributing to Cross.CQRS.EF

Thank you for your interest in the project.

## Quick links

- [Report an issue](https://github.com/denis-peshkov/Cross.CQRS.EF/issues/new/choose)
- [Open PRs](https://github.com/denis-peshkov/Cross.CQRS.EF/pulls)
- [CI (.NET)](https://github.com/denis-peshkov/Cross.CQRS.EF/actions/workflows/dotnet.yml)
- [CI (back-merge master → dev)](https://github.com/denis-peshkov/Cross.CQRS.EF/actions/workflows/backmerge-master-to-dev.yml)
- [Branch policy](https://github.com/denis-peshkov/Cross.CQRS.EF/actions/workflows/branch-policy.yml)
- [Breaking gate](https://github.com/denis-peshkov/Cross.CQRS.EF/actions/workflows/breaking-gate.yml)
- [Triage](https://github.com/denis-peshkov/Cross.CQRS.EF/actions/workflows/triage.yml)
- [SonarCloud](https://sonarcloud.io/summary/new_code?id=Cross.CQRS.EF)
- [NuGet](https://www.nuget.org/packages/Cross.CQRS.EF/)
- [README](README.md)
- [Release notes](docs/CHANGELOG.md)
- Breaking changes: [`docs/BREAKING.md`](docs/BREAKING.md)
- Release readiness: [`docs/RELEASE-PLAN-to-master.md`](docs/RELEASE-PLAN-to-master.md)
- Open backlog: [`docs/TO-DO.md`](docs/TO-DO.md)
- Sibling core library: [Cross.CQRS](https://github.com/denis-peshkov/Cross.CQRS)

---

## What is Cross.CQRS.EF?

**Cross.CQRS.EF** is a NuGet extension for [Cross.CQRS](https://github.com/denis-peshkov/Cross.CQRS):

- EF Core transactional behavior around **commands** (`UnifiedTransactionBehavior`);
- isolation / strategy options (`TransactionBehaviorOptions`) and per-handler `ExactTransaction`;
- DbContext provider wiring via `CqrsRegistrationSyntax.AddEntityFrameworkIntegration<TDbContext>(…)`;
- EF license product metadata (`EfLicenseProductInfo`).

Supported TFMs: **net6.0–net10.0**.

Consumers register core (`AddCQRS`) and this extension, then send requests through MediatR (`IMediator` / `ISender`).

---

## How you can help

| Type | Examples |
|---|---|
| **Report** | Bug with repro steps, expected/actual behavior, package version and TFM |
| **Fix** | Transaction regression, `ExactTransaction`, registration bug, EF licensing slot |
| **Build** | New option/behavior, tests, SampleWebApp improvements |
| **Review** | PR review, especially licensing, DI registration, and transactions |
| **Document** | README, `docs/CHANGELOG.md`, `docs/BREAKING.md`, release plans |

---

## Development principles

### Licensing and security first

Any change to licensing, pipeline behaviors, transactions, or DI registration is **high-priority review**. Do not log or commit license JWTs, private keys, or production secrets. Prefer placeholders in samples and issues. For security-related issues/PRs, include package version and a minimal repro — never real keys or live tokens.

### Public surface is a contract

`AddEntityFrameworkIntegration`, public types, transaction enums/options/attributes, and documented pipeline order are contracts for NuGet consumers. Breaking changes require an entry in `docs/BREAKING.md` only (`config.nuspec` `releaseNotes` links there and must not duplicate the list).

### Minimal diff

Do not mix refactoring, formatting untouched files, and a feature in one PR. Drive-by changes belong in a separate PR.

### Repository conventions

- `.editorconfig` — style source (**UTF-8 BOM**, **LF**, 4 spaces for `.cs`).
- Prefer `GlobalUsings.cs` with `global using` directives (no local `using` in type files). Library project currently uses `ImplicitUsings` = `enable`; test project uses `disable` — follow the project you edit.
- New `.cs` / `.csproj` / `.sln` / `.slnx` files — **UTF-8 with BOM**.
- Tests — **NUnit** + FluentAssertions; prefer method names `Given[X]_When[Y]_Then[Z]` (async → `…Async`); add/update tests with behavior changes.
- Library awaits: `ConfigureAwait(false)` where CA2007 applies; sample/tests may differ (see `.editorconfig`).

---

## In scope / out of scope

### In scope

- `Cross.CQRS.EF/` — library (`Behaviors/`, `Extensions/`, `Options/`, `Enums/`, `Services/`, `Licensing/`);
- `Cross.CQRS.EF.Tests/` — unit / pipeline / integration tests;
- `SampleWebApp/` — smoke host example;
- `README.md`, `docs/CHANGELOG.md`, `docs/BREAKING.md`, `Cross.CQRS.EF/config.nuspec`;
- CI: `.github/workflows/dotnet.yml`, `branch-policy.yml`, `breaking-gate.yml`, `triage.yml`, `backmerge-master-to-dev.yml`.

### Out of scope (without maintainer discussion)

- Changes that belong in **Cross.CQRS** core (`AddCQRS`, FluentValidation scan, core license behavior, request/result filters);
- Large architecture refactors “for aesthetics”;
- New external dependencies without a strong reason;
- Consumer-breaking changes without a `docs/BREAKING.md` entry;
- Secrets, keys, `.env` in commits.

---

## Branches and releases

```
                        ┌──── CI merge ─────────┐     (master → dev, no PR)
feature/* ──┐           ▼                       │
fix/*     ──┼── PR ──► dev ── merge ──► master ─┴─► NuGet + git tag
chore/*   ──┘                              ▲
                                           │
                                 release/* / hotfix/* (owner only)
```

| Branch | Purpose | Who |
|---|---|---|
| `master` | Stable release; GitVersion, **stable** git tag (`vX.Y.Z`), NuGet push | **Owner only** — direct push and PRs |
| `release/*` | Release preparation; NuGet (may be `-preview.*`); **no** git tag for pre-releases | **Owner only** — branch creation and push |
| `hotfix/*` | Urgent production patches; same tag/NuGet rules as `release/*` | **Owner only** — branch creation and push |
| `dev` | Feature integration; NuGet pre-release (`-dev.*`); **never** creates git tags | **Default PR target** for all contributors |
| `feature/*` | New functionality (build/test only — no tag/NuGet) | Contributors |
| `fix/*` | Bug fixes (build/test only — no tag/NuGet) | Contributors |
| `chore/*` | CI, deps, docs-only, maintenance (no tag/NuGet) | Contributors |

Git tags are created only for **stable** `X.Y.Z` (no `-` in `semVer`) on `master` / `release/*` / `hotfix/*`. **`dev` never creates git tags**; it may still push NuGet pre-release packages.

**Access rules (enforced in CI via `.github/workflows/branch-policy.yml`):**

- Contributors open PRs **only into `dev`** from `feature/*`, `fix/*`, or `chore/*`.
- PRs targeting **`master`** — repository owner only (`denis-peshkov`).
- Pushing to **`master`**, **`release/*`**, or **`hotfix/*`** — owner only.
- Release merge `dev` → `master`, tags, and NuGet publish — maintainer step after the release checklist.
- After changes land on **`master`**, CI (`.github/workflows/backmerge-master-to-dev.yml`) **merges `master` into `dev` and pushes** (no PR, no build wait) using the owner PAT secret **`TAGTOKEN`** — required to bypass Protect-dev (PR + `build`). Plain `GITHUB_TOKEN` is rejected (`GH013`). If there are conflicts, the job fails — resolve locally and push to `dev`.

Optional GitHub Rulesets: import recipes from [`.github/rulesets/`](.github/rulesets/).

Versioning: **GitVersion** (`GitVersion.yml`). `dev` is pre-release (`-dev.N`), not a release branch. `commit-message-incrementing: Disabled`.

---

## Branch naming

Prefix + kebab-case description:

| Prefix | When |
|---|---|
| `feature/` | New functionality |
| `fix/` | Bug fix |
| `chore/` | CI, deps, docs-only, maintenance |
| `release/` | Release preparation (owner) |
| `hotfix/` | Urgent production patch (owner) |

Examples:

```
release/11.0.0-short-name
hotfix/critical-transaction-scope
feature/exact-transaction-docs
fix/query-must-not-wrap-transaction
chore/editorconfig-and-templates
```

---

## Commit messages

Use **clear English** messages in imperative/descriptive style:

```
Add ExactTransaction coverage tests
Fix UnifiedTransactionBehavior for nested scopes
Update README transaction options section
```

For breaking changes, explicitly include `BREAKING:` in the commit body or PR title/description.

`docs/CHANGELOG.md` is maintained by maintainers before release (not a contributor checklist item).

---

## Pull request process

### 1. Preparation

```bash
git checkout dev
git pull origin dev
git checkout -b feature/short-description
```

### 2. Changes

- Follow existing folder layout (`Behaviors/`, `Extensions/`, `Options/`, `Enums/`, `Services/`, `Licensing/`, …).
- Do not touch unrelated files.
- Breaking change → `docs/BREAKING.md` only (nuspec keeps a link, not a duplicate list).

### 3. Tests (required)

See [Testing](#testing).

### 4. Open PR

- **Base branch:** `dev` (required for contributors)
- **Do not** open PRs into `master`, `release/*`, or `hotfix/*` unless you are the repository owner
- Description: what, why, how to verify (**English** — for GitHub history and the triage bot)
- For licensing / security / transactions — explicitly note risks
- Breaking consumer change → prefix the **PR title** with `BREAKING:`
- CI detects `BREAKING:` title and/or a `docs/BREAKING.md` diff, adds the `breaking-changes` label, and **fails** until the repository owner adds `breaking-approved` (a comment is not enough)

### 5. CI

Must pass:

- `.NET` workflow (`dotnet build` + `dotnet test` on `Cross.CQRS.EF.slnx`)
- Branch policy (`.github/workflows/branch-policy.yml`) — contributors cannot PR to `master` or push `release/*` / `hotfix/*`
- `Breaking gate` when the PR is consumer-breaking (`BREAKING:` title and/or `docs/BREAKING.md` changed) — owner must add `breaking-approved`
- SonarCloud quality gate on PR (`sonar.qualitygate.wait=true` when enabled)
- Triage PR comment job when enabled (`CURSOR_API_KEY`) — must not fail on large diffs

CodeRabbit (`.coderabbit.yaml`): comment `@coderabbitai full review` when a full pass is needed.

### 6. Review and merge

After approval — merge into `dev`. Release to `master` and NuGet publish is a separate maintainer step.

### One PR rule

**One PR = one feature or one fix.** Split large changes (library + tests → docs → CI).

---

## Testing

### Local run

```bash
dotnet build Cross.CQRS.EF.slnx
dotnet test Cross.CQRS.EF.Tests/Cross.CQRS.EF.Tests.csproj
```

With coverage (OpenCover), as in CI:

```bash
dotnet test Cross.CQRS.EF.Tests/Cross.CQRS.EF.Tests.csproj \
  --collect:"XPlat Code Coverage" \
  --results-directory ./TestResults \
  -- DataCollectionRunSettings.DataCollectors.DataCollector.Configuration.Format=opencover
```

### Pre-PR checklist

- [ ] Tests added/updated for changed behavior (`Given[X]_When[Y]_Then[Z]`; async → `Async`)
- [ ] `dotnet build` / `dotnet test` — green locally
- [ ] For licensing / transactions / registration — prefer pipeline/integration coverage, not only happy path
- [ ] No secrets in code, samples, or test data
- [ ] README / `docs/BREAKING.md` / `Cross.CQRS.EF/config.nuspec` updated when the public surface changes

---

## Documentation

| What changed | Update |
|---|---|
| Public API / registration | `README.md` |
| Breaking change for consumers | `docs/BREAKING.md` only (`config.nuspec` `releaseNotes` = link, no duplicate list) |
| Released behavior | **`docs/CHANGELOG.md` (maintainers, on release work)** and short `config.nuspec` `releaseNotes` (+ link to BREAKING) |
| Packaging / dependencies | `Cross.CQRS.EF/config.nuspec` |
| Release readiness | `docs/RELEASE-PLAN-*.md` |
| Deferred findings | `docs/TO-DO.md` |

---

## License

Code is under [RPL 1.5](LICENSE.md) (Reciprocal Public License). By contributing, you agree that derivative works are distributed under the same terms, or under a [Peshkov commercial license](https://peshkov.biz/license).

There is no separate CLA — merging a PR means agreement with the repository license.

---

## Questions?

- Bugs and features: [GitHub Issues](https://github.com/denis-peshkov/Cross.CQRS.EF/issues)
- Core CQRS / `AddCQRS` issues: [Cross.CQRS](https://github.com/denis-peshkov/Cross.CQRS/issues)

**Thank you for contributing to Cross.CQRS.EF.**
