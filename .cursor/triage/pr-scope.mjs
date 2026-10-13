/**
 * Helpers for PR triage scope: always base...head (all commits), never tip-only.
 */

/**
 * @param {unknown} commits
 * @returns {{ oid: string, messageHeadline: string, authors: string }[]}
 */
export function normalizePrCommits(commits) {
  if (!Array.isArray(commits)) {
    return [];
  }
  return commits.map((c) => {
    const oid = String(c?.oid || c?.sha || '').trim();
    const messageHeadline = String(
      c?.messageHeadline || c?.message || c?.commit?.message || ''
    )
      .split('\n')[0]
      .replace(/\s+/g, ' ')
      .trim();
    const authorsRaw = c?.authors ?? c?.commit?.authors ?? [];
    const authors = (Array.isArray(authorsRaw) ? authorsRaw : [])
      .map((a) => a?.login || a?.name || '')
      .filter(Boolean)
      .join(', ');
    return { oid, messageHeadline, authors };
  });
}

/**
 * Human-readable numbered commit list for the agent prompt.
 * @param {{ oid: string, messageHeadline: string, authors: string }[]} commits
 * @returns {string}
 */
export function formatCommitList(commits) {
  if (!commits.length) {
    return '(no commits listed — still triage full PR file list / diff below)';
  }
  return commits
    .map((c, i) => {
      const short = c.oid ? c.oid.slice(0, 7) : '???????';
      const who = c.authors ? ` (${c.authors})` : '';
      return `${i + 1}. ${short} ${c.messageHeadline || '(no subject)'}${who}`;
    })
    .join('\n');
}

/**
 * Mandatory scope block for the triage agent prompt.
 * @param {{ baseRefName?: string, headRefName?: string, commits?: unknown }} pr
 * @returns {string}
 */
export function formatPrScopeSection(pr) {
  const base = pr?.baseRefName || 'base';
  const head = pr?.headRefName || 'head';
  const commits = normalizePrCommits(pr?.commits);
  const list = formatCommitList(commits);
  return `## Scope (mandatory — full PR, not tip-only)
- Compare: \`${base}...${head}\` (GitHub PR cumulative delta: **all** commits and files in this PR)
- Commits in this PR (${commits.length}):
${list}

Rules:
- Classify category/priority/summary from the **entire** base...head change set above.
- Do **not** triage only the latest push / tip commit.
- Labels must reflect the cumulative PR, not the last synchronize patch alone.
`;
}
