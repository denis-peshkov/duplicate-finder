import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import {
  buildGroupedBullets,
  categorizePath,
  collectDelta,
  formatSection,
  parseArgs,
  pathBullet,
  resolveVersions,
  upsertChangelog,
} from './update-changelog.mjs';

describe('resolveVersions', () => {
  it('returns CLI --version and --from directly when both are set (no tag resolver)', () => {
    const got = resolveVersions({ version: '2.4.0', from: '2.3.0' });
    assert.deepEqual(got, {
      version: '2.4.0',
      from: '2.3.0',
      repositoryLink: '',
    });
  });
});

describe('parseArgs', () => {
  it('defaults to dry-run when --write is absent', () => {
    const args = parseArgs([]);
    assert.equal(args.dryRun, true);
    assert.equal(args.write, false);
  });

  it('enables write alone', () => {
    const args = parseArgs(['--write']);
    assert.equal(args.write, true);
    assert.equal(args.dryRun, false);
  });

  it('lets --dry-run win over --write (no write)', () => {
    const args = parseArgs(['--write', '--dry-run']);
    assert.equal(args.dryRun, true);
    assert.equal(args.write, false);
  });

  it('lets --dry-run win regardless of flag order', () => {
    const args = parseArgs(['--dry-run', '--write']);
    assert.equal(args.dryRun, true);
    assert.equal(args.write, false);
  });
});

describe('categorizePath', () => {
  it('uses repo-agnostic heuristics (no product folder names)', () => {
    assert.equal(categorizePath('Acme.Lib/Foo.cs'), 'Library');
    assert.equal(categorizePath('Acme.Lib/Acme.Lib.csproj'), 'Library');
    assert.equal(categorizePath('Acme.Lib.Tests/Bar.cs'), 'Tests');
    assert.equal(categorizePath('tests/unit/x.cs'), 'Tests');
    assert.equal(categorizePath('samples/Host/Program.cs'), 'Repository tooling');
    assert.equal(categorizePath('.github/workflows/ci.yml'), 'CI / release process');
    assert.equal(categorizePath('GitVersion.yml'), 'Versioning');
    assert.equal(categorizePath('docs/BREAKING.md'), 'Documentation');
  });
});

describe('buildGroupedBullets', () => {
  it('groups paths into changelog categories', () => {
    const groups = buildGroupedBullets({
      paths: [
        '.github/workflows/dotnet.yml',
        'GitVersion.yml',
        'CONTRIBUTING.md',
        '.cursor/skills/gitversion-strategy/scripts/run-matrix.mjs',
        'docs/CHANGELOG.md',
        'Lib/Thing.cs',
        'Lib.Tests/ThingTests.cs',
      ],
      subjects: ['init', 'work', 'update GitVersion configuration'],
    });
    assert.ok(groups['CI / release process']?.length);
    assert.ok(groups.Versioning?.length);
    assert.ok(groups.Documentation?.length);
    assert.ok(groups['Repository tooling']?.length);
    assert.ok(groups.Library?.length);
    assert.ok(groups.Tests?.length);
  });

  it('pathBullet stays path-neutral (no hardcoded release claims)', () => {
    const ci = pathBullet('CI / release process', new Set(['.github/workflows/dotnet.yml']));
    const ver = pathBullet('Versioning', new Set(['GitVersion.yml']));
    const tool = pathBullet('Repository tooling', new Set([
      '.cursor/skills/gitversion-strategy/scripts/run-matrix.mjs',
    ]));
    const docs = pathBullet('Documentation', new Set(['CONTRIBUTING.md']));
    const all = [...ci, ...ver, ...tool, ...docs].join('\n');
    assert.match(ci[0], /dotnet\.yml/);
    assert.match(ver[0], /GitVersion\.yml/);
    assert.match(tool[0], /gitversion-strategy/);
    assert.match(docs[0], /CONTRIBUTING\.md/);
    assert.doesNotMatch(all, /v4\.7\.0|never creates git tags|Inherit|stable-only|golden tests/i);
  });
});

describe('collectDelta', () => {
  it('throws when baseline tag does not resolve', () => {
    assert.throws(
      () => collectDelta('0.0.0-no-such-tag-for-changelog-test'),
      /rev-parse|failed/i,
    );
  });

  it('returns paths/subjects when baseline tag exists', () => {
    const delta = collectDelta('2.3.0');
    assert.ok(Array.isArray(delta.paths));
    assert.ok(Array.isArray(delta.subjects));
  });
});

describe('upsertChangelog', () => {
  const section = formatSection({
    version: '11.1.1',
    date: '13 Sep 2026',
    groups: {
      'CI / release process': ['CI workflow updated.'],
    },
  });

  it('inserts after intro --- when missing', () => {
    const md = '\uFEFF# Changelog\n\nIntro.\n\n---\n\n## v11.1.0 — 13 Sep 2026\n\n- old\n\n---\n';
    const result = upsertChangelog(md, section, '11.1.1');
    assert.equal(result.status, 'inserted');
    assert.ok(result.markdown.startsWith('\uFEFF'));
    assert.match(result.markdown, /## v11\.1\.1 — 13 Sep 2026/);
    assert.ok(result.markdown.indexOf('## v11.1.1') < result.markdown.indexOf('## v11.1.0'));
  });

  it('updates an existing section', () => {
    const first = upsertChangelog(
      '\uFEFF# Changelog\n\n---\n\n## v11.1.0 — 1 Jan 2026\n\n- x\n\n---\n',
      section,
      '11.1.1',
    );
    const second = upsertChangelog(
      first.markdown,
      formatSection({
        version: '11.1.1',
        date: '13 Sep 2026',
        groups: { Versioning: ['GitVersion.yml updated.'] },
      }),
      '11.1.1',
    );
    assert.equal(second.status, 'updated');
    assert.match(second.markdown, /GitVersion\.yml updated/);
    assert.equal((second.markdown.match(/## v11\.1\.1/g) || []).length, 1);
  });

  it('reports up-to-date when identical', () => {
    const base = '\uFEFF# Changelog\n\n---\n\n';
    const once = upsertChangelog(base, section, '11.1.1');
    const twice = upsertChangelog(once.markdown, section, '11.1.1');
    assert.equal(twice.status, 'up-to-date');
  });
});
