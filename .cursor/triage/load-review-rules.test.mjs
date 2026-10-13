import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, rmSync, readdirSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';
import { matchGlob, parseMdcFrontmatter, ruleMatchesPaths, loadMatchedRules } from './load-review-rules.mjs';

test('matchGlob covers ** * prefix and nested segments', () => {
  assert.equal(matchGlob('**/*.cs', 'src/Foo.cs'), true);
  assert.equal(matchGlob('**/*Tests/**/*.cs', 'Project.Tests/Unit/A.cs'), true);
  assert.equal(matchGlob('**/*Test/**/*.cs', 'Project.Test/Bar.cs'), true);
  assert.equal(matchGlob('client/**/*.ts', 'client/app/x.ts'), true);
  assert.equal(matchGlob('client/**/*.ts', 'server/x.ts'), false);
  assert.equal(matchGlob('**/Modules/**/*.cs', 'src/Modules/Feature/Handlers/GetById.cs'), true);
  assert.equal(matchGlob('**/*Context.cs', 'src/MainContext.cs'), true);
});

test('parseMdcFrontmatter reads alwaysApply and globs', () => {
  const raw = `---
description: x
globs:
  - "**/*.cs"
  - 'client/**/*.ts'
alwaysApply: false
---

# Body
ok
`;
  const meta = parseMdcFrontmatter(raw);
  assert.equal(meta.hasFrontmatter, true);
  assert.equal(meta.alwaysApply, false);
  assert.deepEqual(meta.globs, ['**/*.cs', 'client/**/*.ts']);
  assert.match(meta.body, /# Body/);
});

test('parseMdcFrontmatter without frontmatter', () => {
  const meta = parseMdcFrontmatter('# Just text\n');
  assert.equal(meta.hasFrontmatter, false);
  assert.deepEqual(meta.globs, []);
  assert.equal(meta.alwaysApply, undefined);
});

test('ruleMatchesPaths: alwaysApply wins; globs otherwise', () => {
  assert.equal(ruleMatchesPaths({ alwaysApply: true, globs: [] }, []), true);
  assert.equal(
    ruleMatchesPaths({ alwaysApply: false, globs: ['**/*.cs'] }, ['a/b.ts']),
    false
  );
  assert.equal(
    ruleMatchesPaths({ alwaysApply: false, globs: ['**/*.cs'] }, ['a/b.cs']),
    true
  );
  assert.equal(ruleMatchesPaths({ globs: [] }, ['a.cs']), false);
});

test('loadMatchedRules selects alwaysApply and glob hits only', () => {
  const dir = mkdtempSync(join(tmpdir(), 'rules-'));
  try {
    writeFileSync(
      join(dir, '000-global.mdc'),
      `---\nalwaysApply: true\n---\n\n# Global\n`
    );
    writeFileSync(
      join(dir, '102-ef.mdc'),
      `---\nglobs:\n  - "**/*Context.cs"\nalwaysApply: false\n---\n\n# EF\n`
    );
    writeFileSync(
      join(dir, '200-angular.mdc'),
      `---\nglobs:\n  - "client/**/*.ts"\nalwaysApply: false\n---\n\n# Angular\n`
    );
    writeFileSync(join(dir, '100-no-fm.mdc'), `# No frontmatter — skip\n`);

    const hit = loadMatchedRules({
      rulesDir: dir,
      paths: ['src/MainContext.cs'],
    });
    assert.deepEqual(hit.matched, ['000-global.mdc', '102-ef.mdc']);
    assert.match(hit.text, /Global/);
    assert.match(hit.text, /EF/);
    assert.doesNotMatch(hit.text, /Angular/);
    assert.doesNotMatch(hit.text, /No frontmatter/);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('loadMatchedRules returns empty when no rule matches', () => {
  const dir = mkdtempSync(join(tmpdir(), 'rules-empty-'));
  try {
    writeFileSync(
      join(dir, '200-angular.mdc'),
      `---\nglobs:\n  - "client/**/*.ts"\nalwaysApply: false\n---\n\n# Angular\n`
    );
    const hit = loadMatchedRules({
      rulesDir: dir,
      paths: ['src/Foo.cs'],
    });
    assert.deepEqual(hit.matched, []);
    assert.equal(hit.text, '');
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('every project .mdc has frontmatter with alwaysApply or globs', () => {
  const rulesDir = join(dirname(fileURLToPath(import.meta.url)), '..', 'rules');
  const names = readdirSync(rulesDir).filter((name) => name.endsWith('.mdc'));
  assert.ok(names.length > 0);
  for (const name of names) {
    const meta = parseMdcFrontmatter(readFileSync(join(rulesDir, name), 'utf8'));
    assert.equal(meta.hasFrontmatter, true, name);
    assert.equal(typeof meta.alwaysApply, 'boolean', name);
    if (meta.alwaysApply !== true) {
      assert.ok(meta.globs.length > 0, name);
    }
  }
});
