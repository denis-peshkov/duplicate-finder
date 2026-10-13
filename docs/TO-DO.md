# TO-DO (cross-release backlog)

> **Id high-water:** C0 · H2 · M15 · L3

## Критично (безопасность)

---

## Высокий (логика / licensing / auth model)

---

## Средний (противоречия / баги контрактов)

---

## Низкий (техдолг / несогласованности)

### L4. Linux package channels beyond GitHub Release

CI already ships `x86_64-unknown-linux-gnu` `.tar.gz` on Releases. Optional later: AppImage, `.deb` (Debian/Ubuntu), Flatpak/Flathub, and/or AUR — each is a separate distro channel (not a substitute for the Release tarball).

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
- README Settings — только путь к `settings.toml` / логу; ключи TOML не дублируем (настройка через UI).
