// .github/scripts/bot-verified-commits.js
// Verifies that all commits in a pull request are GPG-signed.
// Posts a one-time VerificationBot comment if unverified commits are found.

// Configuration via environment variables
const CONFIG = {
  BOT_NAME: process.env.BOT_NAME || 'VerificationBot',
  BOT_LOGIN: process.env.BOT_LOGIN || 'github-actions',
  COMMENT_MARKER: process.env.COMMENT_MARKER || '[commit-verification-bot]',
  SIGNING_GUIDE_URL: process.env.SIGNING_GUIDE_URL || 
    'https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/sdk_developers/signing.md',
  README_URL: process.env.README_URL || 
    'https://github.com/hiero-ledger/hiero-sdk-python/blob/main/README.md',
  DISCORD_URL: process.env.DISCORD_URL || 
    'https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/discord.md',
  TEAM_NAME: process.env.TEAM_NAME || 'Hiero Python SDK Team',
};

// Sanitizes string input to prevent injection
function sanitizeString(input) {
  if (typeof input !== 'string') return '';
  return input.replace(/[\x00-\x1F\x7F]/g, '').trim();
}

// Validates PR number is a positive integer
function validatePRNumber(prNumber) {
  const num = parseInt(prNumber, 10);
  return Number.isInteger(num) && num > 0 ? num : null;
}

// Fetches commits and counts unverified ones
async function getCommitVerificationStatus(github, owner, repo, prNumber) {
  console.log(`[${CONFIG.BOT_NAME}] Fetching commits for PR #${prNumber}...`);
  
  const commits = await github.paginate(
    github.rest.pulls.listCommits,
    { owner, repo, pull_number: prNumber, per_page: 100 }
  );
  
  const unverifiedCommits = commits.filter(
    commit => commit.commit?.verification?.verified !== true
  );
  
  console.log(`[${CONFIG.BOT_NAME}] Found ${commits.length} total, ${unverifiedCommits.length} unverified`);
  
  return {
    total: commits.length,
    unverified: unverifiedCommits.length,
  };
}

// Checks if bot already posted a verification comment (marker-based detection)
async function hasExistingBotComment(github, owner, repo, prNumber) {
  console.log(`[${CONFIG.BOT_NAME}] Checking for existing bot comments...`);
  
  const comments = await github.paginate(
    github.rest.issues.listComments,
    { owner, repo, issue_number: prNumber, per_page: 100 }
  );
  
  const exists = comments.some(comment => 
    comment.user?.login === CONFIG.BOT_LOGIN &&
    typeof comment.body === 'string' &&
    comment.body.includes(CONFIG.COMMENT_MARKER)
  );
  
  console.log(`[${CONFIG.BOT_NAME}] Existing bot comment: ${exists}`);
  return exists;
}

// Builds the verification failure comment
function buildVerificationComment(commitsUrl) {
  return `${CONFIG.COMMENT_MARKER}
Hi, this is ${CONFIG.BOT_NAME}. 
Your pull request cannot be merged as it has **unverified commits**. 
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

// Posts verification failure comment on the PR
async function postVerificationComment(github, owner, repo, prNumber, commitsUrl) {
  console.log(`[${CONFIG.BOT_NAME}] Posting verification failure comment...`);
  
  await github.rest.issues.createComment({
    owner,
    repo,
    issue_number: prNumber,
    body: buildVerificationComment(commitsUrl),
  });
  
  console.log(`[${CONFIG.BOT_NAME}] Comment posted on PR #${prNumber}`);
  return true;
}

// Main workflow handler
async function main({ github, context }) {
  const { owner, repo } = context.repo;
  const prNumber = validatePRNumber(context.payload?.pull_request?.number);
  
  console.log(`[${CONFIG.BOT_NAME}] Starting verification for ${owner}/${repo} PR #${prNumber}`);
  
  if (!prNumber) {
    console.log(`[${CONFIG.BOT_NAME}] Invalid PR number`);
    return { success: false, unverifiedCount: 0 };
  }
  
  // Get commit verification status
  const { total, unverified } = await getCommitVerificationStatus(github, owner, repo, prNumber);
  
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
    await postVerificationComment(github, owner, repo, prNumber, commitsUrl);
  }
  
  return { success: false, unverifiedCount: unverified };
}

// Exports
module.exports = main;
module.exports.getCommitVerificationStatus = getCommitVerificationStatus;
module.exports.hasExistingBotComment = hasExistingBotComment;
module.exports.postVerificationComment = postVerificationComment;
module.exports.CONFIG = CONFIG;
