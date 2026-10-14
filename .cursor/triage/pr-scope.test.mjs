import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import {
  formatCommitList,
  formatPrScopeSection,
  normalizePrCommits,
} from './pr-scope.mjs';

describe('normalizePrCommits', () => {
  it('maps gh pr view commits shape', () => {
    const out = normalizePrCommits([
      {
        oid: 'abcdef0123456789',
        messageHeadline: 'fix labels',
        authors: [{ login: 'alice' }],
      },
    ]);
    assert.equal(out.length, 1);
    assert.equal(out[0].oid, 'abcdef0123456789');
    assert.equal(out[0].messageHeadline, 'fix labels');
    assert.equal(out[0].authors, 'alice');
  });

  it('returns empty for non-arrays', () => {
    assert.deepEqual(normalizePrCommits(null), []);
  });
});

describe('formatPrScopeSection', () => {
  it('requires full base...head scope and lists every commit', () => {
    const text = formatPrScopeSection({
      baseRefName: 'master',
      headRefName: 'hotfix/x',
      commits: [
        { oid: '1111111aaaaaaaa', messageHeadline: 'first', authors: [{ login: 'a' }] },
        { oid: '2222222bbbbbbbb', messageHeadline: 'second', authors: [{ login: 'b' }] },
      ],
    });
    assert.match(text, /master\.\.\.hotfix\/x/);
    assert.match(text, /Commits in this PR \(2\)/);
    assert.match(text, /1\. 1111111 first/);
    assert.match(text, /2\. 2222222 second/);
    assert.match(text, /Do \*\*not\*\* triage only the latest push/);
    assert.match(text, /cumulative PR/);
  });
});

describe('formatCommitList', () => {
  it('handles empty', () => {
    assert.match(formatCommitList([]), /no commits listed/);
  });
});
