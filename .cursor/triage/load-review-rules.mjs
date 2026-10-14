/**
 * Load Cursor project rules (.mdc) for PR triage by frontmatter
 * (alwaysApply / globs), matching against changed file paths.
 */
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

export const DEFAULT_MAX_RULES_CHARS = 32_000;

/**
 * @param {string} value
 * @returns {string}
 */
export function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Convert a simple gitignore-like / Cursor glob to RegExp.
 * Supports `**`, `*`, `?`; paths use `/`.
 * @param {string} glob
 * @returns {RegExp}
 */
export function globToRegExp(glob) {
  const g = String(glob || '').replace(/\\/g, '/').trim();
  let i = 0;
  let out = '^';
  while (i < g.length) {
    if (g.startsWith('**/', i)) {
      out += '(?:.*/)?';
      i += 3;
      continue;
    }
    if (g[i] === '*' && g[i + 1] === '*') {
      out += '.*';
      i += 2;
      continue;
    }
    if (g[i] === '*') {
      out += '[^/]*';
      i += 1;
      continue;
    }
    if (g[i] === '?') {
      out += '[^/]';
      i += 1;
      continue;
    }
    out += escapeRegExp(g[i]);
    i += 1;
  }
  out += '$';
  return new RegExp(out, 'i');
}

/**
 * @param {string} glob
 * @param {string} filePath
 * @returns {boolean}
 */
export function matchGlob(glob, filePath) {
  const path = String(filePath || '').replace(/\\/g, '/');
  return globToRegExp(glob).test(path);
}

/**
 * @param {string} raw
 * @returns {{ alwaysApply?: boolean, globs: string[], body: string, hasFrontmatter: boolean }}
 */
export function parseMdcFrontmatter(raw) {
  const text = String(raw || '').replace(/^\uFEFF/, '');
  if (!text.startsWith('---')) {
    return { globs: [], body: text, hasFrontmatter: false };
  }

  const end = text.indexOf('\n---', 3);
  if (end === -1) {
    return { globs: [], body: text, hasFrontmatter: false };
  }

  const fm = text.slice(3, end).replace(/^\r?\n/, '');
  const body = text.slice(end + 4).replace(/^\r?\n/, '');
  /** @type {{ alwaysApply?: boolean, globs: string[], body: string, hasFrontmatter: boolean }} */
  const meta = { globs: [], body, hasFrontmatter: true };

  const lines = fm.split(/\r?\n/);
  let inGlobs = false;
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) {
      continue;
    }

    const always = trimmed.match(/^alwaysApply:\s*(true|false)\s*$/i);
    if (always) {
      meta.alwaysApply = always[1].toLowerCase() === 'true';
      inGlobs = false;
      continue;
    }

    if (/^globs:\s*$/i.test(trimmed)) {
      inGlobs = true;
      continue;
    }

    if (inGlobs) {
      const item = trimmed.match(/^-\s*(.+)\s*$/);
      if (item) {
        let value = item[1].trim();
        if (
          (value.startsWith('"') && value.endsWith('"')) ||
          (value.startsWith("'") && value.endsWith("'"))
        ) {
          value = value.slice(1, -1);
        }
        if (value) {
          meta.globs.push(value);
        }
        continue;
      }
      // Non-list line ends globs block
      inGlobs = false;
    }
  }

  return meta;
}

/**
 * @param {{ alwaysApply?: boolean, globs: string[] }} meta
 * @param {string[]} paths
 * @returns {boolean}
 */
export function ruleMatchesPaths(meta, paths) {
  if (meta.alwaysApply === true) {
    return true;
  }
  if (!meta.globs?.length) {
    return false;
  }
  const list = (paths || []).filter(Boolean);
  if (list.length === 0) {
    return false;
  }
  return meta.globs.some((glob) => list.some((p) => matchGlob(glob, p)));
}

/**
 * @param {object} options
 * @param {string} options.rulesDir
 * @param {string[]} options.paths
 * @param {number} [options.maxChars]
 * @returns {{ text: string, matched: string[] }}
 */
export function loadMatchedRules({ rulesDir, paths, maxChars = DEFAULT_MAX_RULES_CHARS }) {
  if (!rulesDir || !existsSync(rulesDir)) {
    return { text: '', matched: [] };
  }

  const names = readdirSync(rulesDir)
    .filter((name) => name.endsWith('.mdc'))
    .sort();

  /** @type {{ name: string, body: string }[]} */
  const selected = [];
  for (const name of names) {
    const raw = readFileSync(join(rulesDir, name), 'utf8');
    const meta = parseMdcFrontmatter(raw);
    if (!ruleMatchesPaths(meta, paths)) {
      continue;
    }
    const body = (meta.body || '').trim();
    if (!body) {
      continue;
    }
    selected.push({ name, body: `### ${name}\n\n${body}` });
  }

  if (selected.length === 0) {
    return { text: '', matched: [] };
  }

  const matched = selected.map((s) => s.name);
  let text = selected.map((s) => s.body).join('\n\n---\n\n');
  if (text.length > maxChars) {
    text = `${text.slice(0, maxChars)}\n\n…(rules truncated for triage prompt size)`;
  }
  return { text, matched };
}
