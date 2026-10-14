import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { flattenPaginated } from './flatten-paginated.mjs';

describe('flattenPaginated', () => {
  it('flattens --slurp page arrays', () => {
    assert.deepEqual(
      flattenPaginated([[{ id: 1 }, { id: 2 }], [{ id: 3 }]]),
      [{ id: 1 }, { id: 2 }, { id: 3 }]
    );
  });

  it('passes through an already-flat item list', () => {
    const items = [{ id: 1 }, { id: 2 }];
    assert.deepEqual(flattenPaginated(items), items);
  });

  it('returns [] for non-arrays', () => {
    assert.deepEqual(flattenPaginated(null), []);
    assert.deepEqual(flattenPaginated({}), []);
  });
});
