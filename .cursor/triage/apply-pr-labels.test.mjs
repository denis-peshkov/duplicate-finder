import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import {
  labelsFromTriage,
  normalizeCategoryLabel,
  normalizePriorityLabel,
  applyPrTriageLabels,
  shouldApplyTriageLabels,
  MANAGED_TRIAGE_LABELS,
  DEFAULT_LABEL_MIN_CONFIDENCE,
} from './apply-pr-labels.mjs';

describe('normalizeCategoryLabel', () => {
  it('accepts known categories', () => {
    assert.equal(normalizeCategoryLabel('Enhancement'), 'enhancement');
    assert.equal(normalizeCategoryLabel('bug'), 'bug');
    assert.equal(normalizeCategoryLabel('docs'), 'docs');
  });

  it('rejects unknown', () => {
    assert.equal(normalizeCategoryLabel('unknown'), null);
    assert.equal(normalizeCategoryLabel(''), null);
  });
});

describe('normalizePriorityLabel', () => {
  it('prefixes priority', () => {
    assert.equal(normalizePriorityLabel('medium'), 'priority:medium');
    assert.equal(normalizePriorityLabel('priority:high'), 'priority:high');
  });

  it('rejects unknown', () => {
    assert.equal(normalizePriorityLabel('urgent'), null);
  });
});

describe('labelsFromTriage', () => {
  it('returns category and priority labels', () => {
    const { toAdd, managed } = labelsFromTriage({
      category: 'enhancement',
      priority: 'medium',
    });
    assert.deepEqual(toAdd, ['enhancement', 'priority:medium']);
    assert.ok(managed.includes('priority:low'));
    assert.equal(managed.length, MANAGED_TRIAGE_LABELS.length);
  });
});

describe('shouldApplyTriageLabels', () => {
  it('defaults to applying labels when env unset (default 1)', () => {
    const gate = shouldApplyTriageLabels({ confidence: 95 }, {});
    assert.equal(gate.apply, true);
  });

  it('opt-out via TRIAGE_APPLY_LABELS=false', () => {
    const gate = shouldApplyTriageLabels(
      { confidence: 95 },
      { TRIAGE_APPLY_LABELS: 'false' }
    );
    assert.equal(gate.apply, false);
    assert.match(gate.reason, /disabled/);
  });

  it('requires confidence floor when enabled', () => {
    const low = shouldApplyTriageLabels({ confidence: 40 }, {});
    assert.equal(low.apply, false);
    assert.equal(low.minConfidence, DEFAULT_LABEL_MIN_CONFIDENCE);

    const ok = shouldApplyTriageLabels(
      { confidence: 80 },
      { TRIAGE_APPLY_LABELS: '1' }
    );
    assert.equal(ok.apply, true);
  });

  it('honors TRIAGE_LABEL_MIN_CONFIDENCE', () => {
    const gate = shouldApplyTriageLabels(
      { confidence: 85 },
      { TRIAGE_LABEL_MIN_CONFIDENCE: '90' }
    );
    assert.equal(gate.apply, false);
    assert.equal(gate.minConfidence, 90);
  });
});

describe('applyPrTriageLabels', () => {
  it('creates missing labels, adds current, then removes stale triage labels', () => {
    /** @type {string[][]} */
    const calls = [];
    const gh = (args, opts) => {
      calls.push(args);
      if (args[0] === 'pr' && args[1] === 'view') {
        assert.equal(opts?.json, true);
        return {
          labels: [
            { name: 'priority:high' },
            { name: 'bug' },
            { name: 'needs-human' },
          ],
        };
      }
      return '';
    };

    const result = applyPrTriageLabels(gh, 42, {
      category: 'enhancement',
      priority: 'medium',
    });

    assert.deepEqual(result.added, ['enhancement', 'priority:medium']);
    assert.deepEqual(result.removed.sort(), ['bug', 'priority:high']);

    const createCalls = calls.filter((c) => c[0] === 'label' && c[1] === 'create');
    assert.equal(createCalls.length, 2);

    const addCallIndex = calls.findIndex(
      (c) => c[0] === 'pr' && c[1] === 'edit' && c.includes('--add-label')
    );
    const removeCallIndex = calls.findIndex(
      (c) => c[0] === 'pr' && c[1] === 'edit' && c.includes('--remove-label')
    );
    assert.ok(addCallIndex >= 0);
    assert.ok(removeCallIndex >= 0);
    assert.ok(addCallIndex < removeCallIndex, 'add labels before remove');

    const addCall = calls[addCallIndex];
    assert.ok(addCall.includes('enhancement'));
    assert.ok(addCall.includes('priority:medium'));

    const removeCall = calls[removeCallIndex];
    assert.ok(removeCall.includes('bug'));
    assert.ok(removeCall.includes('priority:high'));
    assert.ok(!removeCall.includes('needs-human'));
  });
});
