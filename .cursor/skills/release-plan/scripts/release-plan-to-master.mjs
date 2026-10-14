#!/usr/bin/env node
/**
 * Recalculate the "Change summary" line in docs/RELEASE-PLAN-to-master.md.
 *
 * Includes:
 * - table rows with IDs like P1, B1, Q1, N1, A1, G1 (status — last emoji in the table row);
 * - §10 markers (release gate + go/no-go bullets), if present.
 *
 * Usage:
 *   node .cursor/skills/release-plan/scripts/release-plan-to-master.mjs           # print the line
 *   node .cursor/skills/release-plan/scripts/release-plan-to-master.mjs --write   # update the plan file
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '../../../..');
const PLAN = join(ROOT, 'docs/RELEASE-PLAN-to-master.md');

const ID_ROW = /^\| ([A-Z]+[0-9]+) \|/;
const BULLET = /^- (✅|🟨|⬜|❌) /;
/** Canonical label + legacy "Checklist summary" / "Checklist Summary" (replace, do not duplicate). */
const SUMMARY_RE = /^\*\*(?:Change summary|Checklist summary):\*\*.*$/im;

function primaryStatus(cell) {
  return (cell.match(/^(✅|🟨|⬜|❌)/) ?? [])[1] ?? null;
}

function statusFromTableRow(line) {
  const parts = line.split('|').map((c) => c.trim());
  const dataCols = parts.slice(2, -1);
  for (let i = dataCols.length - 1; i >= 0; i--) {
    const status = primaryStatus(dataCols[i]);
    if (status) {
      return status;
    }
  }
  return null;
}

export function collectChecklistStatuses(markdown) {
  const statuses = [];
  /** @type {string | null} */
  let sectionHeading = null;

  for (const line of markdown.split('\n')) {
    const heading = line.match(/^##\s+(.+)/);
    if (heading) {
      sectionHeading = heading[1].trim();
      continue;
    }

    if (ID_ROW.test(line)) {
      const status = statusFromTableRow(line);
      if (!status) {
        throw new Error(`Status not found in checklist row: ${line.slice(0, 120)}`);
      }
      statuses.push(status);
      continue;
    }

    // §10 markers only (release gate + go/no-go) — ignore status bullets elsewhere
    const inSection10 = sectionHeading != null && /^10\b/.test(sectionHeading);
    const bullet = inSection10 ? line.match(BULLET) : null;
    if (bullet) {
      statuses.push(bullet[1]);
    }
  }

  return statuses;
}

export function formatSummaryLine(statuses) {
  const total = statuses.length;
  const counts = { '✅': 0, '🟨': 0, '⬜': 0, '❌': 0 };
  for (const status of statuses) {
    counts[status] += 1;
  }

  const pct = (n) => (total ? Math.round((n / total) * 100) : 0);

  return (
    `**Change summary:** **${total}** items — ` +
    `✅ **${counts['✅']}** (${pct(counts['✅'])}%) · ` +
    `🟨 **${counts['🟨']}** (${pct(counts['🟨'])}%) · ` +
    `⬜ **${counts['⬜']}** (${pct(counts['⬜'])}%) · ` +
    `❌ **${counts['❌']}** (${pct(counts['❌'])}%)`
  );
}

/**
 * Replace existing summary line, or insert before the first `---` / `##` if missing.
 * @param {string} markdown
 * @param {string} line
 * @returns {{ markdown: string; status: 'up-to-date' | 'updated' | 'inserted' }}
 */
export function applySummaryLine(markdown, line) {
  if (SUMMARY_RE.test(markdown)) {
    const updated = markdown.replace(SUMMARY_RE, line);
    if (updated === markdown) {
      return { markdown, status: 'up-to-date' };
    }
    return { markdown: updated, status: 'updated' };
  }

  const hr = markdown.match(/\n---\r?\n/);
  if (hr && hr.index != null) {
    return {
      markdown: `${markdown.slice(0, hr.index)}\n${line}${markdown.slice(hr.index)}`,
      status: 'inserted',
    };
  }

  const heading = markdown.match(/\n##\s/);
  if (heading && heading.index != null) {
    return {
      markdown: `${markdown.slice(0, heading.index)}\n${line}\n${markdown.slice(heading.index)}`,
      status: 'inserted',
    };
  }

  return {
    markdown: `${markdown.replace(/\s*$/, '')}\n\n${line}\n`,
    status: 'inserted',
  };
}

function main() {
  const markdown = readFileSync(PLAN, 'utf8');
  const line = formatSummaryLine(collectChecklistStatuses(markdown));

  if (process.argv.includes('--write')) {
    const { markdown: next, status } = applySummaryLine(markdown, line);
    if (status === 'up-to-date') {
      console.log('Change summary is already up to date');
    } else {
      writeFileSync(PLAN, next, 'utf8');
      console.log(
        status === 'inserted'
          ? `Inserted Change summary in ${PLAN}`
          : `Updated ${PLAN}`
      );
    }
  }

  console.log(line);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main();
}
