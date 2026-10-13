#!/usr/bin/env node
/**
 * CI triage: reads collected gh data + Cursor skills, runs Cursor Agent, writes report.
 * Requires: CURSOR_API_KEY, gh auth (GITHUB_TOKEN in Actions).
 */
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { Agent, CursorAgentError } from '@cursor/sdk';
import { createLocalAgentOptions } from './cursor-agent-local.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '../..');
const DATA = join(ROOT, '.cursor/triage/docs/.data');
const SKILLS = join(ROOT, '.cursor/skills/triage/SKILL.md');
const DATE = new Date().toISOString().slice(0, 10);
const OUT = join(ROOT, `.cursor/triage/docs/ci-report-${DATE}.md`);
const POST_COMMENT = process.env.TRIAGE_POST_COMMENT === 'true';
const MODE = process.env.TRIAGE_MODE || 'audit';

const apiKey = process.env.CURSOR_API_KEY;
if (!apiKey) {
  console.error('CURSOR_API_KEY is required for CI triage agent.');
  process.exit(1);
}

function readDataFile(name) {
  const p = join(DATA, name);
  if (!existsSync(p)) return null;
  return readFileSync(p, 'utf8');
}

function buildPrompt() {
  const skill = existsSync(SKILLS) ? readFileSync(SKILLS, 'utf8') : '';
  const repo = readDataFile('repo.txt')?.trim() ?? 'unknown';
  const issuesOpen = readDataFile('issues-open.json') ?? '[]';
  const issuesClosed = readDataFile('issues-closed.json') ?? '[]';
  const prsOpen = readDataFile('prs-open.json') ?? '[]';
  const collaborators = readDataFile('collaborators.txt') ?? '';
  const prFiles = readDataFile('pr-files.jsonl') ?? '';

  return `You are running automated triage for this GitHub repository (${repo}). See README.md for project layout.

Follow the workflow in the triage skill below.
Mode: ${MODE} (audit = tables + cross-analysis only, no GitHub comments).

## Skill instructions

${skill}

## Collected data (${DATE})

### Collaborators
${collaborators}

### Open issues JSON
${issuesOpen}

### Recently closed issues JSON
${issuesClosed}

### Open PRs JSON
${prsOpen}

### PR files (jsonl)
${prFiles}

## Output requirements

Write a complete markdown triage report in Russian with:
1. Issue triage tables (critical, linked to PR, active, duplicates, stale)
2. PR triage tables (ours, external ready, external problematic)
3. Cross-analysis sections 3.1–3.5 from the skill
4. Numeric summary table
5. Prioritized action list (top 10)

Do NOT post to GitHub. Output only the markdown report body.
Security focus: secrets, auth/licensing, PII, payments, and domain-critical paths from README.md.
`;
}

async function main() {
  mkdirSync(join(ROOT, '.cursor/triage/docs'), { recursive: true });

  const repo = readDataFile('repo.txt')?.trim() ?? 'unknown';
  const prompt = buildPrompt();
  console.log(`Running Cursor agent triage (${MODE})...`);

  try {
    const result = await Agent.prompt(prompt, {
      apiKey,
      model: { id: 'auto' },
      local: createLocalAgentOptions(ROOT),
    });

    if (result.status === 'error' || result.status === 'cancelled') {
      console.error('Agent run failed:', result.id, result.status);
      process.exit(2);
    }

    const body = result.result?.trim() || '# Triage\n\nNo output from agent.';
    const report = `# CI Triage — ${repo} — ${DATE}\n\n${body}\n`;
    writeFileSync(OUT, report, 'utf8');
    console.log(`Report written: ${OUT}`);

    if (POST_COMMENT) {
      await postTriageIssueComment(report);
    }
  } catch (err) {
    if (err instanceof CursorAgentError) {
      console.error('Cursor SDK startup failed:', err.message, 'retryable=', err.isRetryable);
      process.exit(1);
    }
    throw err;
  }
}

async function postTriageIssueComment(report) {
  const { execSync } = await import('node:child_process');
  const gh = join(ROOT, '.cursor/triage/gh-wrapper.sh');
  const title = `CI Triage Report ${DATE}`;
  const body = report.length > 60000 ? report.slice(0, 60000) + '\n\n…(truncated)' : report;

  try {
    const existing = execSync(
      `${gh} issue list --label triage-report --state open --json number,title --limit 5`,
      { cwd: ROOT, encoding: 'utf8' }
    );
    const issues = JSON.parse(existing || '[]');
    const match = issues.find((i) => i.title === title);

    if (match) {
      execSync(`${gh} issue comment ${match.number} --body-file -`, {
        cwd: ROOT,
        input: body,
        stdio: ['pipe', 'inherit', 'inherit'],
      });
      console.log(`Commented on issue #${match.number}`);
    } else {
      execSync(
        `${gh} issue create --title "${title}" --label triage-report --body-file -`,
        { cwd: ROOT, input: body, stdio: ['pipe', 'inherit', 'inherit'] }
      );
      console.log('Created triage-report issue');
    }
  } catch (e) {
    console.warn('Could not post triage issue (non-fatal):', e.message);
  }
}

main();
