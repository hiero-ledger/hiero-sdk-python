/**
 * Bot that comments on PRs with invalid conventional commit titles
 * Provides helpful guidance on fixing the title format
 *
 * @module bot-conventional-pr-title
 */

// Unique identifier to find/update existing bot comments
const COMMENT_IDENTIFIER = '<!-- bot-conventional-pr-title -->';

// Maximum comments to fetch (prevent excessive API usage)
const MAX_COMMENTS_TO_FETCH = 500;

/**
 * Suggest appropriate conventional commit type based on PR title keywords
 * @param {string} title - The PR title to analyze
 * @returns {string} The suggested conventional commit type
 */
function suggestConventionalType(title) {
  console.log('[Bot] Analyzing title for type suggestion:', title);

  if (!title || typeof title !== 'string') {
    console.log('[Bot] ⚠️ Invalid title, defaulting to "chore"');
    return 'chore';
  }

  const lowerTitle = title.toLowerCase();

  // Priority order for keyword matching
  if (lowerTitle.match(/\b(format|formatting|style|prettier|eslint|lint)\b/)) {
    console.log('[Bot] Detected formatting keywords → suggesting "style"');
    return 'style';
  }
  if (lowerTitle.match(/\b(docs|documentation|readme|comment|comments)\b/)) {
    console.log('[Bot] Detected documentation keywords → suggesting "docs"');
    return 'docs';
  }
  if (lowerTitle.match(/\b(fix|bug|issue|error|crash|problem)\b/)) {
    console.log('[Bot] Detected bug fix keywords → suggesting "fix"');
    return 'fix';
  }
  if (lowerTitle.match(/\b(test|testing|spec|unit|integration)\b/)) {
    console.log('[Bot] Detected test keywords → suggesting "test"');
    return 'test';
  }
  if (lowerTitle.match(/\b(refactor|refactoring|restructure|reorganize)\b/)) {
    console.log('[Bot] Detected refactor keywords → suggesting "refactor"');
    return 'refactor';
  }
  if (lowerTitle.match(/\b(perf|performance|optimize|speed)\b/)) {
    console.log('[Bot] Detected performance keywords → suggesting "perf"');
    return 'perf';
  }
  if (lowerTitle.match(/\b(build|compile|dependency|dependencies|deps)\b/)) {
    console.log('[Bot] Detected build keywords → suggesting "build"');
    return 'build';
  }
  if (lowerTitle.match(/\b(ci|workflow|action|pipeline)\b/)) {
    console.log('[Bot] Detected CI keywords → suggesting "ci"');
    return 'ci';
  }

  console.log('[Bot] No specific keywords matched → suggesting "chore"');
  return 'chore';
}

/**
 * Generate the header section of the bot message
 * @param {string} currentTitle - Current PR title
 * @param {string} suggestedType - Suggested conventional type
 * @returns {string} Formatted header
 */
function generateMessageHeader(currentTitle, suggestedType) {
  return `${COMMENT_IDENTIFIER}
## PR Title Needs Conventional Format

**Your current title is:**
\`\`\`
${currentTitle}
\`\`\`

**It needs to have a type prefix like:**
\`\`\`
${suggestedType}: ${currentTitle}
\`\`\`

---
`;
}

/**
 * Generate the fix instructions section
 * @param {string} suggestedType - Suggested conventional type
 * @param {string} escapedTitle - Shell-escaped title
 * @param {number} prNumber - PR number
 * @returns {string} Formatted instructions
 */
function generateFixInstructions(suggestedType, escapedTitle, prNumber) {
  return `### How to Fix This

#### Option 1: Via GitHub UI
1. Go to the top of this PR page
2. Click on the title to edit it
3. Add the type prefix (e.g., \`${suggestedType}:\`) before your current title
4. Save the changes

#### Option 2: Via Command Line
\`\`\`bash
# Note: Adjust the title as needed if it contains special characters
gh pr edit ${prNumber} --title "${suggestedType}: ${escapedTitle}"
\`\`\`

---
`;
}

/**
 * Generate the valid types reference section
 * @returns {string} Formatted types list
 */
function generateValidTypesList() {
  return `### Valid Conventional Commit Types
- \`feat\` - New feature
- \`fix\` - Bug fix
- \`docs\` - Documentation changes
- \`style\` - Code style changes (formatting, missing semi-colons, etc)
- \`refactor\` - Code refactoring
- \`perf\` - Performance improvements
- \`test\` - Adding or updating tests
- \`build\` - Build system changes
- \`ci\` - CI configuration changes
- \`chore\` - Other changes that don't modify src or test files
- \`revert\` - Reverts a previous commit

📖 Learn more: [Conventional Commits](https://www.conventionalcommits.org/)
`;
}

/**
 * Format the bot comment message with title guidance
 * @param {string} currentTitle - The current PR title
 * @param {string} suggestedType - The suggested conventional type
 * @param {number} prNumber - The PR number
 * @returns {string} Formatted markdown message
 */
function formatMessage(currentTitle, suggestedType, prNumber) {
  console.log('[Bot] Formatting message with suggestion:', suggestedType);

  // Escape shell-sensitive characters for the CLI example
  const escapedTitle = currentTitle.replace(/["$`\\]/g, '\\$&');

  // Compose message from smaller components
  return generateMessageHeader(currentTitle, suggestedType) +
         generateFixInstructions(suggestedType, escapedTitle, prNumber) +
         generateValidTypesList();
}

/**
 * Main bot execution function
 * @param {Object} params - Function parameters
 * @param {Object} params.github - GitHub API client
 * @param {Object} params.context - GitHub Actions context
 * @param {number} params.prNumber - Pull request number
 * @param {string} params.prTitle - Pull request title
 * @param {boolean} [params.dryRun=false] - Dry run mode flag
 * @returns {Promise<void>}
 */
async function run({ github, context, prNumber, prTitle, dryRun = false }) {
  try {
    console.log('='.repeat(60));
    console.log('[Bot] Starting conventional PR title bot');
    console.log('[Bot] Dry Run Mode:', dryRun);
    console.log('[Bot] PR Number:', prNumber);
    console.log('[Bot] PR Title:', prTitle);
    console.log('[Bot] Repository:', `${context.repo.owner}/${context.repo.repo}`);
    console.log('='.repeat(60));

    // Validate inputs
    if (!prNumber || typeof prNumber !== 'number') {
      console.error('[Bot] ❌ Invalid PR number:', prNumber);
      throw new Error('Invalid PR number provided');
    }

    if (!prTitle || typeof prTitle !== 'string') {
      console.error('[Bot] ❌ Invalid PR title:', prTitle);
      throw new Error('Invalid PR title provided');
    }

    // Suggest appropriate conventional type
    const suggestedType = suggestConventionalType(prTitle);

    // Format the bot message
    const message = formatMessage(prTitle, suggestedType, prNumber);

    console.log('[Bot] Fetching PR comments with pagination...');

    // Fetch comments with pagination and early exit
    let comments = [];
    let page = 1;
    let botComment = null;

    while (comments.length < MAX_COMMENTS_TO_FETCH && !botComment) {
      const response = await github.rest.issues.listComments({
        owner: context.repo.owner,
        repo: context.repo.repo,
        issue_number: prNumber,
        per_page: 100,
        page: page
      });

      comments = comments.concat(response.data);

      // Check if we found the bot comment
      botComment = response.data.find(comment =>
        comment.body && comment.body.includes(COMMENT_IDENTIFIER)
      );

      // Exit if no more pages or found the comment
      if (response.data.length < 100 || botComment) {
        break;
      }

      page++;
    }

    console.log(`[Bot] Fetched ${comments.length} comments across ${page} page(s)`);

    if (dryRun) {
      console.log('='.repeat(60));
      console.log('[Bot] 🔍 DRY RUN MODE - No changes will be made');
      console.log('[Bot] Would suggest type:', suggestedType);
      console.log('[Bot] Bot comment exists:', !!botComment);
      console.log('[Bot] Action that would be taken:', botComment ? 'UPDATE' : 'CREATE');
      console.log('='.repeat(60));
      return;
    }

    if (botComment) {
      console.log('[Bot] Found existing bot comment, updating...');
      console.log('[Bot] Comment ID:', botComment.id);

      await github.rest.issues.updateComment({
        owner: context.repo.owner,
        repo: context.repo.repo,
        comment_id: botComment.id,
        body: message,
      });

      console.log('[Bot] ✅ Successfully updated existing comment');
    } else {
      console.log('[Bot] No existing bot comment found, creating new one...');

      const response = await github.rest.issues.createComment({
        owner: context.repo.owner,
        repo: context.repo.repo,
        issue_number: prNumber,
        body: message,
      });

      console.log('[Bot] ✅ Successfully created new comment');
      console.log('[Bot] Comment ID:', response.data.id);
    }

    console.log('='.repeat(60));
    console.log('[Bot] Bot execution completed successfully');
    console.log('='.repeat(60));

  } catch (error) {
    console.error('='.repeat(60));
    console.error('[Bot] ❌ Error occurred during bot execution');

    // Handle permission errors gracefully
    if (error.status === 403) {
      console.error('[Bot] Permission denied - bot lacks write access to this repository');
      console.error('[Bot] This is expected for fork PRs and will not fail the workflow');
      console.error('[Bot] The bot will function normally once the PR is on the main repository');
      console.error('='.repeat(60));
      return; // Exit gracefully, don't fail the workflow
    }

    // Log other errors with details
    console.error('[Bot] Error name:', error.name);
    console.error('[Bot] Error message:', error.message);
    console.error('[Bot] Error status:', error.status);
    console.error('[Bot] Error stack:', error.stack);
    console.error('='.repeat(60));
    throw error;
  }
}

// Export functions for testing and workflow usage
module.exports = {
  run,
  suggestConventionalType,
  formatMessage
};
