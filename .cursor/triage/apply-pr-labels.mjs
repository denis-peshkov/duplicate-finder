/**
 * Apply GitHub labels from automated PR triage (category + priority).
 * Manages only known triage labels; other labels on the PR are left untouched.
 *
 * Labels sync by default when confidence ≥ `TRIAGE_LABEL_MIN_CONFIDENCE`
 * (default 70). Set `TRIAGE_APPLY_LABELS=false` to disable. Category/priority
 * stay allowlisted. Comment suggestions are independent of this gate.
 */

export const CATEGORY_LABELS = Object.freeze([
  'feature',
  'bug',
  'enhancement',
  'security',
  'docs',
  'chore',
]);

export const PRIORITY_VALUES = Object.freeze(['critical', 'high', 'medium', 'low']);

/** @type {ReadonlyArray<string>} */
export const MANAGED_TRIAGE_LABELS = Object.freeze([
  ...CATEGORY_LABELS,
  ...PRIORITY_VALUES.map((p) => `priority:${p}`),
]);

export const DEFAULT_LABEL_MIN_CONFIDENCE = 70;

const LABEL_META = Object.freeze({
  feature: { color: '0e8a16', description: 'New API or behavior' },
  bug: { color: 'e8372a', description: 'Something is broken' },
  enhancement: { color: 'a2eeef', description: 'Polish, perf, or DX without new public contract' },
  security: {
    color: '5319e7',
    description: '🔒 Auth/JWT/OAuth, secrets, licensing, PII, payment, or token security',
  },
  docs: { color: '006b75', description: 'Improvements or additions to documentation' },
  chore: { color: '1d76db', description: 'Build, CI, tooling, deps' },
  'priority:critical': { color: 'b60205', description: 'Triage priority: critical' },
  'priority:high': { color: 'd93f0b', description: 'Triage priority: high' },
  'priority:medium': { color: 'fb8500', description: 'Triage priority: medium' },
  'priority:low': { color: 'fbca04', description: 'Triage priority: low' },
});

/**
 * @param {unknown} value
 * @returns {string | null}
 */
export function normalizeCategoryLabel(value) {
  const raw = String(value || '')
    .trim()
    .toLowerCase();
  if (!raw || raw === 'unknown') {
    return null;
  }
  return CATEGORY_LABELS.includes(raw) ? raw : null;
}

/**
 * @param {unknown} value
 * @returns {string | null} label like priority:medium
 */
export function normalizePriorityLabel(value) {
  const raw = String(value || '')
    .trim()
    .toLowerCase()
    .replace(/^priority:/, '');
  if (!PRIORITY_VALUES.includes(raw)) {
    return null;
  }
  return `priority:${raw}`;
}

/**
 * @param {{ category?: unknown; priority?: unknown }} data
 * @returns {{ toAdd: string[]; managed: readonly string[] }}
 */
export function labelsFromTriage(data) {
  const category = normalizeCategoryLabel(data?.category);
  const priority = normalizePriorityLabel(data?.priority);
  return {
    toAdd: [category, priority].filter(Boolean),
    managed: MANAGED_TRIAGE_LABELS,
  };
}

/**
 * Gate: labels on by default; opt-out via TRIAGE_APPLY_LABELS=false|0|no|off.
 * Also requires confidence floor (allowlist is in labelsFromTriage).
 *
 * @param {{ confidence?: unknown }} data
 * @param {NodeJS.ProcessEnv} [env]
 * @returns {{ apply: boolean; reason: string; confidence: number; minConfidence: number }}
 */
export function shouldApplyTriageLabels(data, env = process.env) {
  const flag = String(env.TRIAGE_APPLY_LABELS ?? '1')
    .trim()
    .toLowerCase();
  const disabled = flag === 'false' || flag === '0' || flag === 'no' || flag === 'off';
  const enabled = !disabled;
  const parsedMin = Number(env.TRIAGE_LABEL_MIN_CONFIDENCE);
  const minConfidence =
    Number.isFinite(parsedMin) && parsedMin >= 0
      ? Math.min(100, parsedMin)
      : DEFAULT_LABEL_MIN_CONFIDENCE;
  const confidence = Math.min(100, Math.max(0, Number(data?.confidence) || 0));

  if (!enabled) {
    return {
      apply: false,
      reason: 'TRIAGE_APPLY_LABELS is disabled (comment-only suggestions)',
      confidence,
      minConfidence,
    };
  }

  if (confidence < minConfidence) {
    return {
      apply: false,
      reason: `confidence ${confidence} < min ${minConfidence}`,
      confidence,
      minConfidence,
    };
  }

  return {
    apply: true,
    reason: 'enabled and confidence gate passed',
    confidence,
    minConfidence,
  };
}

/**
 * @param {(args: string[], opts?: { json?: boolean }) => unknown} gh
 * @param {string} name
 */
function ensureLabel(gh, name) {
  const meta = LABEL_META[name] || { color: 'ededed', description: 'Triage label' };
  try {
    gh([
      'label',
      'create',
      name,
      '--color',
      meta.color,
      '--description',
      meta.description,
      '--force',
    ]);
  } catch (err) {
    console.warn(`ensureLabel(${name}):`, err?.message ?? err);
  }
}

/**
 * Sync triage labels on a PR: drop previous managed triage labels, set current ones.
 * Caller must gate with {@link shouldApplyTriageLabels} before invoking.
 *
 * @param {(args: string[], opts?: { json?: boolean }) => unknown} gh
 * @param {number|string} prNumber
 * @param {{ category?: unknown; priority?: unknown }} data
 * @returns {{ added: string[]; removed: string[] }}
 */
export function applyPrTriageLabels(gh, prNumber, data) {
  const { toAdd, managed } = labelsFromTriage(data);
  const pr = String(prNumber);

  if (toAdd.length === 0) {
    console.warn('No valid triage category/priority — skipping label sync');
    return { added: [], removed: [] };
  }

  const view = /** @type {{ labels?: { name: string }[] }} */ (
    gh(['pr', 'view', pr, '--json', 'labels'], { json: true })
  );
  const currentNames = (view.labels ?? []).map((l) => l.name);

  const toRemove = currentNames.filter(
    (name) => managed.includes(name) && !toAdd.includes(name)
  );

  for (const name of toAdd) {
    ensureLabel(gh, name);
  }

  gh(['pr', 'edit', pr, ...toAdd.flatMap((name) => ['--add-label', name])]);

  if (toRemove.length > 0) {
    gh(['pr', 'edit', pr, ...toRemove.flatMap((name) => ['--remove-label', name])]);
  }

  return { added: toAdd, removed: toRemove };
}
