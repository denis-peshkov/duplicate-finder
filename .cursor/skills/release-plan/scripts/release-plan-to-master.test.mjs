import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { applySummaryLine, formatSummaryLine } from './release-plan-to-master.mjs';

const sampleLine = formatSummaryLine(['✅', '⬜']);

describe('formatSummaryLine', () => {
  it('uses canonical Change summary label', () => {
    assert.match(sampleLine, /^\*\*Change summary:\*\*/);
  });
});

describe('applySummaryLine', () => {
  it('reports up-to-date when the line already matches', () => {
    const md = `# Plan\n\n${sampleLine}\n\n---\n`;
    const result = applySummaryLine(md, sampleLine);
    assert.equal(result.status, 'up-to-date');
    assert.equal(result.markdown, md);
  });

  it('updates when the line exists but differs', () => {
    const md = `# Plan\n\n**Change summary:** **0** items — ✅ **0** (0%) · 🟨 **0** (0%) · ⬜ **0** (0%) · ❌ **0** (0%)\n\n---\n`;
    const result = applySummaryLine(md, sampleLine);
    assert.equal(result.status, 'updated');
    assert.match(result.markdown, new RegExp(`^${escapeRegExp(sampleLine)}$`, 'm'));
  });

  it('replaces legacy Checklist summary (any case) without duplicating', () => {
    for (const label of ['Checklist summary', 'Checklist Summary']) {
      const md = `# Plan\n\n**${label}:** **0** items — ✅ **0** (0%) · 🟨 **0** (0%) · ⬜ **0** (0%) · ❌ **0** (0%)\n\n---\n`;
      const result = applySummaryLine(md, sampleLine);
      assert.equal(result.status, 'updated');
      assert.match(result.markdown, /^\*\*Change summary:\*\*/m);
      assert.equal((result.markdown.match(/\*\*(?:Change|Checklist) summary:\*\*/gi) || []).length, 1);
    }
  });

  it('inserts before --- when the line is missing (not "up to date")', () => {
    const md = `# Plan\n\n> meta\n\n---\n\n## 1. Preconditions\n`;
    const result = applySummaryLine(md, sampleLine);
    assert.equal(result.status, 'inserted');
    assert.ok(result.markdown.includes(`${sampleLine}\n---`));
    assert.ok(!result.markdown.includes('already up to date'));
  });
});

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
