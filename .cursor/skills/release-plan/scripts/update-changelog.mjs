#!/usr/bin/env node
/**
 * Upsert docs/CHANGELOG.md section for the target release (newest-first).
 *
 * Derives English bullets from git name-status + filtered commit subjects
 * between from_version (default: latest stable tag) and HEAD.
 *
 * Usage:
 *   node .cursor/skills/release-plan/scripts/update-changelog.mjs --write
 *   node .cursor/skills/release-plan/scripts/update-changelog.mjs --version 11.1.1 --from 11.1.0 --write
 *   node .cursor/skills/release-plan/scripts/update-changelog.mjs --dry-run
 */
import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(SCRIPT_DIR, '../../../..');
const CHANGELOG_PATH = join(ROOT, 'docs', 'CHANGELOG.md');
const BOM = '\uFEFF';

const NOISE_COMMIT = /^(init|work|d2|wip|tmp|temp|merge\b)/i;

const CATEGORY_ORDER = [
  'CI / release process',
  'Versioning',
  'Library',
  'Tests',
  'Documentation',
  'Repository tooling',
];

/**
 * Build the CLI help text for this script.
 * @returns {string} Multi-line usage string printed for `-h` / `--help`.
 */
function usage() {
  return `Usage:
  node .cursor/skills/release-plan/scripts/update-changelog.mjs [options]

Options:
  --version X.Y.Z   Target version (default: resolve-target-version.sh)
  --from X.Y.Z      Base published version / tag without v (default: from resolve)
                    When both --version and --from are set, skips the tag resolver.
  --changelog PATH  CHANGELOG path (default: docs/CHANGELOG.md)
  --date TEXT       Heading date (default: local "D Mon YYYY")
  --write           Write docs/CHANGELOG.md
  --dry-run         Print section only (default if no --write; wins over --write)
  -h, --help        Show help`;
}

/**
 * Parse CLI argv into options for changelog generation.
 * Any `--dry-run` forces `write: false` even when `--write` is also present.
 * @param {string[]} argv Process argv without `node` / script path.
 * @returns {{ version: string|null, from: string|null, changelog: string, date: string|null, write: boolean, dryRun: boolean }}
 */
export function parseArgs(argv) {
  const args = {
    version: null,
    from: null,
    changelog: CHANGELOG_PATH,
    date: null,
    write: false,
    dryRun: false,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '-h' || a === '--help') {
      console.log(usage());
      process.exit(0);
    }
    if (a === '--write') {
      args.write = true;
      continue;
    }
    if (a === '--dry-run') {
      args.dryRun = true;
      continue;
    }
    if (a === '--version' || a === '--from' || a === '--changelog' || a === '--date') {
      const v = argv[++i];
      if (v == null) throw new Error(`missing value for ${a}`);
      if (a === '--version') args.version = v;
      else if (a === '--from') args.from = v;
      else if (a === '--changelog') args.changelog = resolve(v);
      else args.date = v;
      continue;
    }
    throw new Error(`unknown arg: ${a}`);
  }
  // Any --dry-run forbids write (print section only), even if --write was also passed.
  if (args.dryRun) {
    args.write = false;
  } else if (!args.write) {
    args.dryRun = true;
  }
  return args;
}

/**
 * Run a synchronous subprocess under the repo root (or `cwd`).
 * @param {string} cmd Executable name or path.
 * @param {string[]} cmdArgs Arguments for the executable.
 * @param {{ cwd?: string, check?: boolean }} [options] `check` (default true) throws on non-zero exit.
 * @returns {{ status: number, stdout: string, stderr: string }}
 */
function run(cmd, cmdArgs, { cwd = ROOT, check = true } = {}) {
  const p = spawnSync(cmd, cmdArgs, { cwd, encoding: 'utf8' });
  if (check && p.status !== 0) {
    const err = (p.stderr || p.stdout || '').trim();
    throw new Error(`${cmd} ${cmdArgs.join(' ')} failed: ${err || `exit ${p.status}`}`);
  }
  return {
    status: p.status ?? 1,
    stdout: p.stdout || '',
    stderr: p.stderr || '',
  };
}

/**
 * Resolve target/from SemVer via `resolve-target-version.sh` (optional CLI overrides).
 * When both `--version` and `--from` are set, return them directly (no tag/GitVersion resolver).
 * @param {{ version?: string|null, from?: string|null }} opts Parsed CLI version/from fields.
 * @returns {{ version: string, from: string, repositoryLink: string }}
 */
export function resolveVersions({ version, from }) {
  if (version && from) {
    return { version, from, repositoryLink: '' };
  }
  const script = join(SCRIPT_DIR, 'resolve-target-version.sh');
  const cli = [];
  if (version) cli.push('--version', version);
  const out = run('bash', [script, '--json', ...cli]);
  const meta = JSON.parse(out.stdout.trim());
  return {
    version: version || meta.target_version,
    from: from || meta.from_version,
    repositoryLink: meta.repository_link,
  };
}

/**
 * Format a local date as `D Mon YYYY` for CHANGELOG headings.
 * @param {Date} [d=new Date()] Date to format.
 * @returns {string}
 */
function formatDate(d = new Date()) {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${d.getDate()} ${months[d.getMonth()]} ${d.getFullYear()}`;
}

/**
 * Strip a leading UTF-8 BOM if present.
 * @param {string} text Input text.
 * @returns {string}
 */
function stripBom(text) {
  return text.charCodeAt(0) === 0xfeff ? text.slice(1) : text;
}

/**
 * Ensure the string starts with a UTF-8 BOM (repo CHANGELOG convention).
 * @param {string} text Input text.
 * @returns {string}
 */
function ensureBom(text) {
  return text.startsWith(BOM) ? text : BOM + text;
}

/**
 * True when a path looks like a test project / test tree (repo-agnostic).
 * @param {string} path Repo-relative path.
 * @returns {boolean}
 */
function isTestPath(path) {
  return /(^|\/)[^/]*\.?Tests(\/|$)/.test(path) || /(^|\/)tests?\//i.test(path);
}

/**
 * True when a path looks like product/library source (not tests/samples/docs/CI).
 * @param {string} path Repo-relative path.
 * @returns {boolean}
 */
function isLibraryPath(path) {
  if (isTestPath(path)) return false;
  const top = path.split('/')[0] || '';
  if (/^(Sample|samples?|demo|examples?)/i.test(top)) return false;
  if (path.startsWith('docs/') || path.startsWith('.github/') || path.startsWith('.cursor/')) return false;
  return /\.(cs|csproj|fs|fsproj|vb|vbproj|nuspec)$/i.test(path);
}

/**
 * Map a repo-relative path to a CHANGELOG category, or null to skip.
 * Heuristics only — no hard-coded product folder names.
 * @param {string} path File path relative to the repository root.
 * @returns {string|null} Category name from {@link CATEGORY_ORDER}, or null.
 */
export function categorizePath(path) {
  if (!path || path === 'docs/CHANGELOG.md') return null;
  if (path.startsWith('.github/workflows/') || path.startsWith('.github/')) return 'CI / release process';
  if (path === 'GitVersion.yml') return 'Versioning';
  if (isTestPath(path)) return 'Tests';
  if (isLibraryPath(path)) return 'Library';
  if (
    path === 'CONTRIBUTING.md' ||
    path === 'README.md' ||
    path.startsWith('docs/')
  ) {
    return 'Documentation';
  }
  if (path.startsWith('.cursor/') || path === '.gitignore') return 'Repository tooling';
  return 'Repository tooling';
}

/**
 * Build neutral path-only CHANGELOG bullets for one category (no invented release claims).
 * @param {string} category Category heading (e.g. `Versioning`).
 * @param {Set<string>|Iterable<string>} paths Paths belonging to that category.
 * @returns {string[]} One or more bullet bodies (without leading `- `).
 */
export function pathBullet(category, paths) {
  // Neutral path-only bullets — never invent release-specific claims from filenames.
  // Release-specific wording: refine manually (or derive from diff later) after --write.
  const filtered = [...paths].filter((p) => !/^docs\/RELEASE-PLAN/.test(p) && p !== 'docs/TO-DO.md');
  const use = filtered.length ? filtered : [...paths];
  const sample = [...use].sort().slice(0, 8);
  const more = use.length > sample.length ? ` (+${use.length - sample.length} more)` : '';
  const list = sample.map((p) => `\`${p}\``).join(', ');
  const prefixes = {
    'CI / release process': 'CI / GitHub Actions paths updated',
    Versioning: 'Versioning config updated',
    Library: 'Library sources changed',
    Tests: 'Tests updated',
    Documentation: 'Docs updated',
    'Repository tooling': 'Repo tooling updated',
  };
  const prefix = prefixes[category] || 'Updated';
  return [`${prefix}: ${list}${more}.`];
}

/**
 * Collect changed paths and commit subjects from `v{from}..HEAD` (+ working tree paths).
 * Fails hard if the baseline tag does not resolve or if `git diff` / `git log` fail.
 * @param {string} fromVersion Baseline SemVer with or without a leading `v`.
 * @returns {{ paths: string[], subjects: string[] }}
 */
export function collectDelta(fromVersion) {
  if (!fromVersion || typeof fromVersion !== 'string') {
    throw new Error('collectDelta: fromVersion is required');
  }
  const tag = fromVersion.startsWith('v') ? fromVersion : `v${fromVersion}`;
  // Fail hard if the baseline tag is missing — never invent an empty delta.
  run('git', ['rev-parse', '--verify', `${tag}^{commit}`]);

  const range = `${tag}..HEAD`;
  const names = run('git', ['diff', '--name-only', range]);
  const paths = names.stdout
    .split('\n')
    .map((s) => s.trim())
    .filter(Boolean);

  // Uncommitted / index paths also count for the working tree release draft.
  const wt = run('git', ['status', '--porcelain', '-u'], { check: false });
  if (wt.status === 0) {
    for (const line of wt.stdout.split('\n')) {
      const p = line.slice(3).trim().split(' -> ').pop();
      if (p) paths.push(p);
    }
  }

  const log = run('git', ['log', range, '--pretty=format:%s']);
  const subjects = log.stdout
    .split('\n')
    .map((s) => s.trim())
    .filter(Boolean);

  return { paths: [...new Set(paths)], subjects };
}

/**
 * Heuristic CHANGELOG category for a commit subject (used when folding commits into groups).
 * @param {string} subject Commit subject line.
 * @returns {string|null} Category name, or null if no match.
 */
function subjectCategory(subject) {
  const s = subject.toLowerCase();
  if (s.includes('workflow') || s.includes('actions') || s.includes('nuget') || /\bci\b/.test(s) || s.includes('git tag')) {
    return 'CI / release process';
  }
  if (s.includes('gitversion.yml') || (s.includes('gitversion') && (s.includes('increment') || s.includes('config')))) {
    return 'Versioning';
  }
  if (s.includes('changelog') || s.includes('contributing') || s.includes('readme') || s.includes('docs')) {
    return 'Documentation';
  }
  if (s.includes('test')) return 'Tests';
  if (s.includes('skill') || s.includes('matrix') || s.includes('runner') || s.includes('.gitignore')) {
    return 'Repository tooling';
  }
  if (s.includes('gitversion')) return 'Versioning';
  return null;
}

/**
 * Group delta paths (and optionally commit subjects) into CHANGELOG category → bullets.
 * @param {{ paths: string[], subjects: string[], includeCommits?: boolean }} input
 * @returns {Record<string, string[]>} Map of category name to bullet bodies.
 */
export function buildGroupedBullets({ paths, subjects, includeCommits = false }) {
  /** @type {Map<string, Set<string>>} */
  const byCat = new Map();
  for (const p of paths) {
    const cat = categorizePath(p);
    if (!cat) continue;
    if (!byCat.has(cat)) byCat.set(cat, new Set());
    byCat.get(cat).add(p);
  }

  /** @type {Record<string, string[]>} */
  const groups = {};
  for (const cat of CATEGORY_ORDER) {
    const set = byCat.get(cat);
    if (!set?.size) continue;
    groups[cat] = [...pathBullet(cat, set)];
  }

  const notable = subjects
    .filter((s) => !NOISE_COMMIT.test(s))
    .filter((s) => !/^Merge /i.test(s))
    .map((s) => s.replace(/\s+/g, ' ').trim())
    .filter(Boolean);

  // Path-first; optionally fold a few commit subjects into matching categories.
  if (includeCommits || Object.keys(groups).length === 0) {
    for (const s of notable.slice(0, 8)) {
      const cat = subjectCategory(s) || (Object.keys(groups).length === 0 ? 'Repository tooling' : null);
      if (!cat) continue;
      const line = s.endsWith('.') ? s : `${s}.`;
      if (!groups[cat]) groups[cat] = [];
      if (!groups[cat].some((b) => b.toLowerCase() === line.toLowerCase())) {
        groups[cat].push(line);
      }
    }
  }

  return groups;
}

/**
 * Render a newest-first CHANGELOG section markdown block for one version.
 * @param {{ version: string, date: string, groups: Record<string, string[]> }} input
 * @returns {string} Section ending with `---` and a trailing blank line.
 */
export function formatSection({ version, date, groups }) {
  const lines = [`## v${version} — ${date}`, ''];
  for (const cat of CATEGORY_ORDER) {
    const bullets = groups[cat];
    if (!bullets?.length) continue;
    lines.push(`### ${cat}`, '');
    for (const b of bullets) {
      lines.push(`- ${b}`);
    }
    lines.push('');
  }
  if (lines.length === 2) {
    lines.push('### Repository tooling', '', '- Release housekeeping.', '');
  }
  lines.push('---');
  return `${lines.join('\n')}\n\n`;
}

/**
 * Insert or replace the `## v{version}` section in CHANGELOG markdown (newest-first).
 * Preserves / restores UTF-8 BOM.
 * @param {string} markdown Full CHANGELOG file contents.
 * @param {string} section Formatted section from {@link formatSection}.
 * @param {string} version Target SemVer without leading `v`.
 * @returns {{ status: 'inserted'|'updated'|'up-to-date', markdown: string, section: string }}
 */
export function upsertChangelog(markdown, section, version) {
  const hadBom = markdown.charCodeAt(0) === 0xfeff;
  let body = stripBom(markdown).replace(/\r\n/g, '\n');
  if (!body.endsWith('\n')) body += '\n';

  const headingRe = new RegExp(`^## v${version.replace(/\./g, '\\.')}(?:\\s|$)`, 'm');
  const nextHeadingRe = /^## v/gm;

  let nextBody;
  let status;
  if (headingRe.test(body)) {
    // Replace from this heading through the line before the next ## v… (or EOF).
    const start = body.search(headingRe);
    nextHeadingRe.lastIndex = start + 1;
    const next = nextHeadingRe.exec(body);
    const end = next ? next.index : body.length;
    const existing = body.slice(start, end);
    const normalizedSection = section.endsWith('\n') ? section : `${section}\n`;
    if (existing === normalizedSection) {
      status = 'up-to-date';
      nextBody = body;
    } else {
      status = 'updated';
      nextBody = body.slice(0, start) + normalizedSection + body.slice(end);
    }
  } else {
    status = 'inserted';
    // Insert after the first horizontal rule that ends the intro.
    const introHr = body.indexOf('\n---\n');
    if (introHr === -1) {
      nextBody = `${body.trimEnd()}\n\n${section}`;
    } else {
      const at = introHr + '\n---\n'.length;
      nextBody = body.slice(0, at) + '\n' + section + body.slice(at).replace(/^\n*/, '');
    }
  }

  const out = hadBom || true ? ensureBom(nextBody) : nextBody;
  return { status, markdown: out, section };
}

/**
 * CLI entry: resolve versions, collect delta, print or write the CHANGELOG section.
 * @returns {void}
 */
function main() {
  const args = parseArgs(process.argv.slice(2));
  const { version, from } = resolveVersions(args);
  const date = args.date || formatDate();
  const delta = collectDelta(from);
  const groups = buildGroupedBullets(delta);
  const section = formatSection({ version, date, groups });

  if (args.dryRun) {
    process.stdout.write(section);
    return;
  }

  if (!existsSync(args.changelog)) {
    throw new Error(`missing changelog: ${args.changelog}`);
  }
  const prev = readFileSync(args.changelog, 'utf8');
  const result = upsertChangelog(prev, section, version);
  writeFileSync(args.changelog, result.markdown, 'utf8');
  console.error(`${result.status}: docs/CHANGELOG.md § v${version} (from v${from})`);
}

const isMain = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) {
  try {
    main();
  } catch (err) {
    console.error(String(err?.stack || err));
    process.exit(1);
  }
}
