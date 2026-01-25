// .github/scripts/bot-verified-commits.js
// Verifies that all commits in a pull request are GPG-signed.
// Posts a one-time VerificationBot comment if unverified commits are found.

// Sanitizes string input to prevent injection (uses Unicode property escape per Biome lint)
function sanitizeString(input) {
  if (typeof input !== 'string') return '';
  return input.replace(/\p{Cc}/gu, '').trim();
}

// Escapes markdown special characters and breaks @mentions to prevent injection
// Required per CodeRabbit review: commit messages are user-controlled and can cause
// markdown injection or unwanted @mentions that spam teams
function sanitizeMarkdown(input) {
  return sanitizeString(input)
    .replace(/[\x60*_~[\]()]/g, '\\$&')  // Escape markdown special chars (backtick via hex)
    .replace(/@/g, '@\u200b');           // Break @mentions with zero-width space
}


// Validates URL format and returns fallback if invalid
function sanitizeUrl(input, fallback) {
  const cleaned = sanitizeString(input);
  return /^https?:\/\/[^\s]+$/i.test(cleaned) ? cleaned : fallback;
}

// Configuration via environment variables (sanitized)
const CONFIG = {
  BOT_NAME: sanitizeString(process.env.BOT_NAME) || 'VerificationBot',
  BOT_LOGIN: sanitizeString(process.env.BOT_LOGIN) || 'github-actions',
  COMMENT_MARKER: sanitizeString(process.env.COMMENT_MARKER) || '[commit-verification-bot]',
  SIGNING_GUIDE_URL: sanitizeUrl(
    process.env.SIGNING_GUIDE_URL,
    'https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/sdk_developers/signing.md'
  ),
  README_URL: sanitizeUrl(
    process.env.README_URL,
    'https://github.com/hiero-ledger/hiero-sdk-python/blob/main/README.md'
  ),
  DISCORD_URL: sanitizeUrl(
    process.env.DISCORD_URL,
    'https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/discord.md'
  ),
  TEAM_NAME: sanitizeString(process.env.TEAM_NAME) || 'Hiero Python SDK Team',
  MAX_PAGES: (() => {
    const parsed = Number.parseInt(process.env.MAX_PAGES ?? '5', 10);
    return Number.isInteger(parsed) && parsed > 0 ? parsed : 5;
  })(),
  DRY_RUN: process.env.DRY_RUN === 'true',
};

// Validates PR number is a positive integer
function validatePRNumber(prNumber) {
  const num = parseInt(prNumber, 10);
  return Number.isInteger(num) && num > 0 ? num : null;
}

// Fetches commits with bounded pagination and counts unverified ones
async function getCommitVerificationStatus(github, owner, repo, prNumber) {
  console.log(`[${CONFIG.BOT_NAME}] Fetching commits for PR #${prNumber}...`);
  
  const commits = [];
  let page = 0;
  let truncated = false;
  
  try {
    for await (const response of github.paginate.iterator(
      github.rest.pulls.listCommits,
      { owner, repo, pull_number: prNumber, per_page: 100 }
    )) {
      commits.push(...response.data);
      if (++page >= CONFIG.MAX_PAGES) {
        truncated = true;
        console.warn(`[${CONFIG.BOT_NAME}] Reached MAX_PAGES (${CONFIG.MAX_PAGES}) limit`);
        break;
      }
    }
  } catch (error) {
    console.error(`[${CONFIG.BOT_NAME}] Failed to list commits`, {
      owner,
      repo,
      prNumber,
      status: error?.status,
      message: error?.message,
    });
    throw error;
  }
  
  const unverifiedCommits = commits.filter(
    commit => commit.commit?.verification?.verified !== true
  );
  
  console.log(`[${CONFIG.BOT_NAME}] Found ${commits.length} total, ${unverifiedCommits.length} unverified`);
  
  // Fail-closed: if truncated and no unverified found, treat as potentially unverified
  const unverifiedCount = truncated && unverifiedCommits.length === 0
    ? 1
    : unverifiedCommits.length;
  
  return {
    total: commits.length,
    unverified: unverifiedCount,
    unverifiedCommits,
    truncated,
  };
}

// Checks if bot already posted a verification comment (marker-based detection)
// Uses bounded pagination and early return for efficiency
async function hasExistingBotComment(github, owner, repo, prNumber) {
  console.log(`[${CONFIG.BOT_NAME}] Checking for existing bot comments...`);
  
  // Support both with and without [bot] suffix for GitHub Actions bot account
  const botLogins = new Set([
    CONFIG.BOT_LOGIN,
    `${CONFIG.BOT_LOGIN}[bot]`,
    'github-actions[bot]',
  ]);
  
  let page = 0;
  try {
    for await (const response of github.paginate.iterator(
      github.rest.issues.listComments,
      { owner, repo, issue_number: prNumber, per_page: 100 }
    )) {
      // Early return if marker found
      if (response.data.some(comment =>
        botLogins.has(comment.user?.login) &&
        typeof comment.body === 'string' &&
        comment.body.includes(CONFIG.COMMENT_MARKER)
      )) {
        console.log(`[${CONFIG.BOT_NAME}] Existing bot comment: true`);
        return true;
      }
      if (++page >= CONFIG.MAX_PAGES) {
        // Fail-safe: assume comment exists to prevent duplicates
        console.warn(
          `[${CONFIG.BOT_NAME}] Reached MAX_PAGES (${CONFIG.MAX_PAGES}) limit; assuming existing comment to avoid duplicates`
        );
        return true;
      }
    }
  } catch (error) {
    console.error(`[${CONFIG.BOT_NAME}] Failed to list comments`, {
      owner,
      repo,
      prNumber,
      status: error?.status,
      message: error?.message,
    });
    throw error;
  }
  
  console.log(`[${CONFIG.BOT_NAME}] Existing bot comment: false`);
  return false;
}

// Builds the verification failure comment with unverified commit details
function buildVerificationComment(
  commitsUrl,
  unverifiedCommits = [],
  unverifiedCount = unverifiedCommits.length,
  truncated = false
) {
  // Build list of unverified commits (show first 10 max)
  const maxDisplay = 10;
  const commitList = unverifiedCommits.length
    ? unverifiedCommits.slice(0, maxDisplay).map(c => {
        const sha = c.sha?.substring(0, 7) || 'unknown';
        const msg = sanitizeMarkdown(c.commit?.message?.split('\n')[0] || 'No message').substring(0, 50);
        return `- \`${sha}\` ${msg}`;
      }).join('\n')
    : (truncated ? '- Unable to enumerate commits due to pagination limit.' : '');
  
  const moreCommits = unverifiedCommits.length > maxDisplay 
    ? `\n- ...and ${unverifiedCommits.length - maxDisplay} more` 
    : '';

  const countText = truncated ? `at least ${unverifiedCount}` : `${unverifiedCount}`;
  const truncationNote = truncated
    ? '\n\n> ⚠️ Verification scanned only the first pages of commits due to pagination limits. Please review the commits tab.'
    : '';

  return `${CONFIG.COMMENT_MARKER}
Hi, this is ${CONFIG.BOT_NAME}. 
Your pull request cannot be merged as it has **${countText} unverified commit(s)**:

${commitList}${moreCommits}${truncationNote}

View your commit verification status: [Commits Tab](${sanitizeString(commitsUrl)}).

To achieve verified status, please read:
- [Signing guide](${CONFIG.SIGNING_GUIDE_URL})
- [README](${CONFIG.README_URL})
- [Discord](${CONFIG.DISCORD_URL})

Remember, you require a GPG key and each commit must be signed with:
\`git commit -S -s -m "Your message here"\`

Thank you for contributing!

From the ${CONFIG.TEAM_NAME}`;
}

// Posts verification failure comment on the PR with error handling
async function postVerificationComment(
  github,
  owner,
  repo,
  prNumber,
  commitsUrl,
  unverifiedCommits,
  unverifiedCount,
  truncated
) {
  // Skip posting in dry-run mode
  if (CONFIG.DRY_RUN) {
    console.log(`[${CONFIG.BOT_NAME}] DRY_RUN enabled; skipping comment.`);
    return true;
  }

  console.log(`[${CONFIG.BOT_NAME}] Posting verification failure comment...`);
  
  try {

    await github.rest.issues.createComment({
      owner,
      repo,
      issue_number: prNumber,
      body: buildVerificationComment(commitsUrl, unverifiedCommits, unverifiedCount, truncated),
    });
    console.log(`[${CONFIG.BOT_NAME}] Comment posted on PR #${prNumber}`);
    return true;
  } catch (error) {
    console.error(`[${CONFIG.BOT_NAME}] Failed to post comment`, {
      owner,
      repo,
      prNumber,
      status: error?.status,
      message: error?.message,
    });
    return false;
  }
}

// Main workflow handler with full validation and error handling
async function main({ github, context }) {
  const owner = sanitizeString(context.repo?.owner);
  const repo = sanitizeString(context.repo?.repo);
  // Support PR_NUMBER env var for workflow_dispatch, fallback to context payload
  const prNumber = validatePRNumber(
    process.env.PR_NUMBER || context.payload?.pull_request?.number
  );
  const repoPattern = /^[A-Za-z0-9_.-]+$/;
  
  // Validate repo context
  if (!repoPattern.test(owner) || !repoPattern.test(repo)) {
    console.error(`[${CONFIG.BOT_NAME}] Invalid repo context`, { owner, repo });
    return { success: false, unverifiedCount: 0 };
  }
  
  console.log(`[${CONFIG.BOT_NAME}] Starting verification for ${owner}/${repo} PR #${prNumber}`);
  
  if (!prNumber) {
    console.log(`[${CONFIG.BOT_NAME}] Invalid PR number`);
    return { success: false, unverifiedCount: 0 };
  }
  
  try {
    // Get commit verification status
    const { total, unverified, unverifiedCommits, truncated } = 
      await getCommitVerificationStatus(github, owner, repo, prNumber);
    
    // All commits verified - success
    if (unverified === 0) {
      console.log(`[${CONFIG.BOT_NAME}] ✅ All ${total} commits are verified`);
      return { success: true, unverifiedCount: 0 };
    }
    
    // Some commits unverified
    console.log(`[${CONFIG.BOT_NAME}] ❌ Found ${unverified} unverified commits`);
    
    // Check for existing comment to avoid duplicates
    const existingComment = await hasExistingBotComment(github, owner, repo, prNumber);
    
    if (existingComment) {
      console.log(`[${CONFIG.BOT_NAME}] Bot already commented. Skipping duplicate.`);
    } else {
      const commitsUrl = `https://github.com/${owner}/${repo}/pull/${prNumber}/commits`;
      await postVerificationComment(
        github,
        owner,
        repo,
        prNumber,
        commitsUrl,
        unverifiedCommits,
        unverified,
        truncated
      );
    }
    
    return { success: false, unverifiedCount: unverified };
  } catch (error) {
    console.error(`[${CONFIG.BOT_NAME}] Verification failed`, {
      owner,
      repo,
      prNumber,
      message: error?.message,
      status: error?.status,
    });
    return { success: false, unverifiedCount: 0 };
  }
}

// Exports
module.exports = main;
module.exports.getCommitVerificationStatus = getCommitVerificationStatus;
module.exports.hasExistingBotComment = hasExistingBotComment;
module.exports.postVerificationComment = postVerificationComment;
module.exports.CONFIG = CONFIG;
