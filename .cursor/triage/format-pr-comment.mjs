/**
 * Renders automated PR triage comment from agent JSON (category, priority, confidence).
 */

import { execFileSync } from 'node:child_process';

export const TRIAGE_MARKER = '<!-- triage -->';

const PRIORITY_EMOJI = {
  critical: '🔴',
  high: '🟠',
  medium: '🟡',
  low: '🟢',
};

/**
 * @param {string} [fallback]
 * @returns {string}
 */
export function resolveRepo(fallback = '') {
  const fromEnv = process.env.GITHUB_REPOSITORY?.trim();
  if (fromEnv) {
    return fromEnv;
  }

  try {
    const url = execFileSync('git', ['remote', 'get-url', 'origin'], {
      encoding: 'utf8',
    }).trim();
    const match = url.match(/github\.com[:/](.+?)(?:\.git)?\/?$/);
    if (match) {
      return match[1];
    }
  } catch {
    // ignore — use fallback
  }

  return fallback;
}

/**
 * @param {string} repo nameWithOwner
 * @returns {string}
 */
export function displayRepoName(repo) {
  if (!repo) {
    return 'Repository';
  }

  const slash = repo.lastIndexOf('/');
  return slash >= 0 ? repo.slice(slash + 1) : repo;
}

/**
 * Optional icon via TRIAGE_ICON_REL_PATH (path in repo, e.g. icon.png).
 *
 * @param {string} repo nameWithOwner
 * @param {string} branch default branch (master, dev, …)
 * @returns {string | null}
 */
export function getTriageIconUrl(repo, branch = 'master') {
  const rel = process.env.TRIAGE_ICON_REL_PATH?.trim();
  if (!rel || !repo) {
    return null;
  }

  return `https://raw.githubusercontent.com/${repo}/${branch}/${rel}`;
}

/**
 * @param {{
 *   category: string;
 *   priority: string;
 *   confidence: number;
 *   summary: string;
 *   maintainerHint?: string;
 *   relevantFiles?: string[];
 *   securityNotes?: string;
 * }} data
 * @param {{ repo?: string; defaultBranch?: string }} [options]
 */
export function formatPrTriageComment(data, options = {}) {
  const category = String(data.category || 'unknown').toLowerCase();
  const priority = String(data.priority || 'medium').toLowerCase();
  const confidence = Math.min(100, Math.max(0, Number(data.confidence) || 0));
  const summary = String(data.summary || 'No summary generated.').trim();
  const files = Array.isArray(data.relevantFiles) ? data.relevantFiles.filter(Boolean) : [];

  const priorityEmoji = PRIORITY_EMOJI[priority] || '🟡';

  const maintainerHint = data.maintainerHint?.trim();
  const maintainerHintBlock = maintainerHint
    ? `> ${maintainerHint.startsWith('>') ? maintainerHint.slice(1).trim() : maintainerHint}\n`
    : '';

  const filesList =
    files.length > 0
      ? files.map((f) => `- \`${f}\``).join('\n')
      : '- _(none identified)_';

  const securityNotes = data.securityNotes?.trim();
  const securityBlock = securityNotes
    ? `\n### Security notes\n\n${securityNotes}\n`
    : '';

  const repo = options.repo || resolveRepo();
  const displayName = displayRepoName(repo);
  const branch = options.defaultBranch || process.env.TRIAGE_ICON_BRANCH || 'master';
  const iconUrl = getTriageIconUrl(repo, branch);
  const repoUrl = repo ? `https://github.com/${repo}` : 'https://github.com';

  const header = iconUrl
    ? `> <img src="${iconUrl}" width="48" height="48" alt="${displayName}"> **${displayName}** · Automated triage by AI`
    : `> **${displayName}** · Automated triage by AI`;

  return `${header}

## 🔍 Automated Triage

| | |
|---|---|
| ✨ **Category** | \`${category}\` |
| ${priorityEmoji} **Priority** | \`${priority}\` |
| 🎯 **Confidence** | ${confidence}% |

### Summary

${summary}

${maintainerHintBlock}
<details>
<summary>📁 Relevant files</summary>

${filesList}

</details>
${securityBlock}
---
*Triaged automatically by [${displayName}](${repoUrl}) · [Cursor](https://cursor.com)* · This is an automated analysis, not a human review.
${TRIAGE_MARKER}
`;
}

/**
 * @param {string} text
 */
export function parseAgentJson(text) {
  const trimmed = text.trim();
  try {
    return JSON.parse(trimmed);
  } catch {
    const fence = trimmed.match(/```(?:json)?\s*([\s\S]*?)```/);
    if (fence) {
      return JSON.parse(fence[1].trim());
    }
    const start = trimmed.indexOf('{');
    const end = trimmed.lastIndexOf('}');
    if (start >= 0 && end > start) {
      return JSON.parse(trimmed.slice(start, end + 1));
    }
    throw new Error('Agent did not return valid JSON');
  }
}
