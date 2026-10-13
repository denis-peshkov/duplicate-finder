import { mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { JsonlLocalAgentStore } from '@cursor/sdk';

/**
 * Local agent options for Node 20.x (no built-in node:sqlite).
 * @param {string} repoRoot repository root (cwd for the agent)
 */
export function createLocalAgentOptions(repoRoot) {
  const storeRoot = join(repoRoot, '.cursor/triage/docs/.data/cursor-sdk-store');
  mkdirSync(storeRoot, { recursive: true });

  return {
    cwd: repoRoot,
    store: new JsonlLocalAgentStore(storeRoot),
  };
}
