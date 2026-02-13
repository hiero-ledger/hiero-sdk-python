#!/usr/bin/env node

/**
 * Workflow Failure Notifier - Looks up PR and posts failure notification
 * DRY_RUN controls behaviour:
 *   DRY_RUN = 1 -> simulate only (no changes, just logs)
 *   DRY_RUN = 0 -> real actions (post PR comments)
 */

const { spawnSync } = require('child_process');
const process = require('process');

// Configuration constants
const MARKER = '<!-- workflowbot:workflow-failure-notifier -->';
const MAX_PAGES = 10; // Safety bound for comment pagination

// Documentation links (edit these when URLs change)
const DOC_SIGNING = 'https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/sdk_developers/signing.md';
const DOC_CHANGELOG = 'https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/sdk_developers/changelog_entry.md';
const DOC_MERGE_CONFLICTS = 'https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/sdk_developers/merge_conflicts.md';
const DOC_REBASING = 'https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/sdk_developers/rebasing.md';
const DOC_TESTING = 'https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/sdk_developers/testing.md';
const DOC_DISCORD = 'https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/discord.md';
const COMMUNITY_CALLS = 'https://zoom-lfx.platform.linuxfoundation.org/meetings/hiero?view=week';

/**
 * Execute gh CLI command safely
 * @param {string[]} args - Arguments array for gh command
 * @param {boolean} silent - Whether to suppress output
 * @returns {string} - Command output
 */
function ghCommand(args = [], silent = false) {
  try {
    const result = spawnSync('gh', args, {
      encoding: 'utf8',
      stdio: silent ? 'pipe' : ['pipe', 'pipe', 'pipe'],
      shell: false
    });
    
    if (result.error) {
      throw result.error;
    }
    
    if (result.status !== 0 && !silent) {
      throw new Error(`Command failed with exit code ${result.status}`);
    }
    
    return (result.stdout || '').trim();
  } catch (error) {
    if (!silent) {
      throw error;
    }
    return '';
  }
}

/**
 * Check if gh CLI exists
 * @returns {boolean}
 */
function ghExists() {
  try {
    if (process.platform === 'win32') {
      const result = spawnSync('where', ['gh'], {
        encoding: 'utf8',
        stdio: 'pipe',
        shell: false
      });
      return result.status === 0;
    } else {
      const result = spawnSync('which', ['gh'], {
        encoding: 'utf8',
        stdio: 'pipe',
        shell: false
      });
      return result.status === 0;
    }
  } catch {
    return false;
  }
}

/**
 * Normalise DRY_RUN input ("true"/"false" -> 1/0, case-insensitive)
 * @param {string|number} value - Input value
 * @returns {number} - Normalised value (0 or 1)
 */
function normaliseDryRun(value) {
  const strValue = String(value).toLowerCase();
  
  if (strValue === '1' || strValue === '0') {
    return parseInt(strValue);
  }
  
  if (strValue === 'true') {
    return 1;
  }
  
  if (strValue === 'false') {
    return 0;
  }
  
  console.error(`ERROR: DRY_RUN must be one of: true, false, 1, 0 (got: ${value})`);
  process.exit(1);
}

// Validate required environment variables
let FAILED_WORKFLOW_NAME = process.env.FAILED_WORKFLOW_NAME || '';
let FAILED_RUN_ID = process.env.FAILED_RUN_ID || '';
let GH_TOKEN = process.env.GH_TOKEN || process.env.GITHUB_TOKEN || '';
const REPO = process.env.REPO || process.env.GITHUB_REPOSITORY || '';
let DRY_RUN = normaliseDryRun(process.env.DRY_RUN || '1');
let PR_NUMBER = process.env.PR_NUMBER || '';

// Set GH_TOKEN environment variable for gh CLI
if (GH_TOKEN) {
  process.env.GH_TOKEN = GH_TOKEN;
}

// Validate required variables or set defaults in dry-run mode
if (!FAILED_WORKFLOW_NAME) {
  if (DRY_RUN === 1) {
    console.log('WARN: FAILED_WORKFLOW_NAME not set, using default for dry-run.');
    FAILED_WORKFLOW_NAME = 'DRY_RUN_TEST';
  } else {
    console.error('ERROR: FAILED_WORKFLOW_NAME environment variable not set.');
    process.exit(1);
  }
}

if (!FAILED_RUN_ID) {
  if (DRY_RUN === 1) {
    console.log('WARN: FAILED_RUN_ID not set, using default for dry-run.');
    FAILED_RUN_ID = '12345';
  } else {
    console.error('ERROR: FAILED_RUN_ID environment variable not set.');
    process.exit(1);
  }
}

// Validate FAILED_RUN_ID is numeric (always check when provided)
if (!/^\d+$/.test(FAILED_RUN_ID)) {
  console.error(`ERROR: FAILED_RUN_ID must be a numeric integer (got: '${FAILED_RUN_ID}')`);
  process.exit(1);
}

// Validate PR_NUMBER if provided
if (PR_NUMBER && PR_NUMBER !== 'null' && !/^\d+$/.test(PR_NUMBER)) {
  console.error(`ERROR: PR_NUMBER must be a numeric integer (got: '${PR_NUMBER}')`);
  process.exit(1);
}

if (!GH_TOKEN) {
  if (DRY_RUN === 1) {
    console.log('WARN: GH_TOKEN not set. Some dry-run operations may fail.');
  } else {
    console.error('ERROR: GH_TOKEN (or GITHUB_TOKEN) environment variable not set.');
    process.exit(1);
  }
}

if (!REPO) {
  console.error('ERROR: REPO environment variable not set.');
  process.exit(1);
}

console.log('------------------------------------------------------------');
console.log(' Workflow Failure Notifier');
console.log(` Repo:                ${REPO}`);
console.log(` Failed Workflow:     ${FAILED_WORKFLOW_NAME}`);
console.log(` Failed Run ID:       ${FAILED_RUN_ID}`);
console.log(` DRY_RUN:             ${DRY_RUN}`);
console.log('------------------------------------------------------------');

// Quick gh availability/auth checks
if (!ghExists()) {
  console.error('ERROR: gh CLI not found. Install it and ensure it\'s on PATH.');
  process.exit(1);
}

try {
  ghCommand(['auth', 'status'], true);
} catch (error) {
  if (DRY_RUN === 0) {
    console.error('ERROR: gh authentication required for non-dry-run mode.');
    process.exit(1);
  } else {
    console.log(`WARN: gh auth status failed — some dry-run operations may not work. (${error.message})`);
  }
}

// PR lookup logic - use PR_NUMBER from workflow_run payload if available, otherwise fallback to branch-based approach
console.log('Looking up PR for failed workflow run...');

// Use PR_NUMBER from workflow_run payload if provided (optimized path)
if (PR_NUMBER && PR_NUMBER !== 'null') {
  console.log(`Using PR number from workflow_run payload: ${PR_NUMBER}`);
} else {
  console.log('PR_NUMBER not provided, falling back to branch-based lookup...');

  let HEAD_BRANCH = '';
  try {
    HEAD_BRANCH = ghCommand(['run', 'view', FAILED_RUN_ID, '--repo', REPO, '--json', 'headBranch', '--jq', '.headBranch'], true);
  } catch {
    HEAD_BRANCH = '';
  }

  if (!HEAD_BRANCH) {
    if (DRY_RUN === 1) {
      console.log('WARN: Could not retrieve head branch in dry-run mode (run ID may be invalid). Exiting gracefully.');
      process.exit(0);
    } else {
      console.error(`ERROR: Could not retrieve head branch from workflow run ${FAILED_RUN_ID}`);
      process.exit(1);
    }
  }

  console.log(`Found head branch: ${HEAD_BRANCH}`);

  // Validate branch name format
  if (HEAD_BRANCH.startsWith('-') || !/^[\w.\/-]+$/.test(HEAD_BRANCH)) {
    console.error(`ERROR: HEAD_BRANCH contains invalid characters: ${HEAD_BRANCH}`);
    process.exit(1);
  }

  // Find PR number for this branch (only open PRs)
  try {
    PR_NUMBER = ghCommand(['pr', 'list', '--repo', REPO, '--head', HEAD_BRANCH, '--json', 'number', '--jq', '.[0].number'], true);
  } catch {
    PR_NUMBER = '';
  }

  if (!PR_NUMBER) {
    if (DRY_RUN === 1) {
      console.log(`No PR associated with workflow run ${FAILED_RUN_ID}, but DRY_RUN=1 - exiting successfully.`);
      process.exit(0);
    } else {
      console.log(`INFO: No open PR found for branch '${HEAD_BRANCH}' (workflow run ${FAILED_RUN_ID}). Nothing to notify.`);
      process.exit(0);
    }
  }
}

console.log(`Found PR #${PR_NUMBER}`);

// Build notification message with failure details and documentation links
const COMMENT = `${MARKER}
Hi, this is WorkflowBot. 
Your pull request cannot be merged as it is not passing all our workflow checks. 
Please click on each check to review the logs and resolve issues so all checks pass.
To help you:
- [DCO signing guide](${DOC_SIGNING})
- [Changelog guide](${DOC_CHANGELOG})
- [Merge conflicts guide](${DOC_MERGE_CONFLICTS})
- [Rebase guide](${DOC_REBASING})
- [Testing guide](${DOC_TESTING})
- [Discord](${DOC_DISCORD})
- [Community Calls](${COMMUNITY_CALLS})
Thank you for contributing!
From the Hiero Python SDK Team`;

// Check for duplicate comments using the correct endpoint for issue comments
let PAGE = 1;
let DUPLICATE_EXISTS = false;

while (PAGE <= MAX_PAGES) {
  let COMMENTS_PAGE = '';
  try {
    COMMENTS_PAGE = ghCommand(['api', '--header', 'Accept: application/vnd.github.v3+json', `/repos/${REPO}/issues/${PR_NUMBER}/comments?per_page=100&page=${PAGE}`], true);
  } catch (error) {
    console.log(`WARN: Failed to fetch comments page ${PAGE}: ${error.message}`);
    COMMENTS_PAGE = '[]';
  }

  // Parse JSON
  let comments = [];
  try {
    comments = JSON.parse(COMMENTS_PAGE);
  } catch (error) {
    console.log(`WARN: Failed to parse comments JSON on page ${PAGE}: ${error.message}`);
    comments = [];
  }

  // Check if the page is empty (no more comments)
  if (comments.length === 0) {
    break;
  }

  // Check this page for the marker
  const foundDuplicate = comments.some(comment => {
    return comment.body && comment.body.includes(MARKER);
  });

  if (foundDuplicate) {
    DUPLICATE_EXISTS = true;
    console.log('Found existing duplicate comment. Skipping.');
    break;
  }

  PAGE++;
}

if (!DUPLICATE_EXISTS) {
  console.log('No existing duplicate comment found.');
}

// Dry-run mode or actual posting
if (DRY_RUN === 1) {
  console.log(`[DRY RUN] Would post comment to PR #${PR_NUMBER}:`);
  console.log('----------------------------------------');
  console.log(COMMENT);
  console.log('----------------------------------------');
  if (DUPLICATE_EXISTS) {
    console.log('[DRY RUN] Would skip posting due to duplicate comment');
  } else {
    console.log('[DRY RUN] Would post new comment (no duplicates found)');
  }
} else {
  if (DUPLICATE_EXISTS) {
    console.log('Comment already exists, skipping.');
  } else {
    console.log(`Posting new comment to PR #${PR_NUMBER}...`);
    
    try {
      ghCommand(['pr', 'comment', PR_NUMBER, '--repo', REPO, '--body', COMMENT]);
      console.log(`Successfully posted comment to PR #${PR_NUMBER}`);
    } catch (error) {
      console.error(`ERROR: Failed to post comment to PR #${PR_NUMBER}`);
      console.error(error.message);
      process.exit(1);
    }
  }
}

console.log('------------------------------------------------------------');
console.log(' Workflow Failure Notifier Complete');
console.log(` DRY_RUN: ${DRY_RUN}`);
console.log('------------------------------------------------------------');
