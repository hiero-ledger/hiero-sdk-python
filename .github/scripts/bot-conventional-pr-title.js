/**
 * Bot that provides automated guidance for PR titles.
 *
 * Provides automated suggestions for fixing non-conventional PR titles.
 *
 * @module bot-conventional-pr-title
 */

const MAX_COMMENTS_TO_FETCH = 500;
const COMMENT_IDENTIFIER = '<!-- bot-conventional-pr-title -->';

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

  // Keyword patterns mapped to conventional types (priority order)
  const typePatterns = [
    { type: 'style', pattern: /\b(format|formatting|style|prettier|eslint|lint)\b/, label: 'formatting' },
    { type: 'docs', pattern: /\b(docs|documentation|readme|comment|comments)\b/, label: 'documentation' },
    { type: 'fix', pattern: /\b(fix|bug|issue|error|crash|problem)\b/, label: 'bug fix' },
    { type: 'test', pattern: /\b(test|testing|spec|unit|integration)\b/, label: 'test' },
    { type: 'refactor', pattern: /\b(refactor|refactoring|restructure|reorganize)\b/, label: 'refactor' },
    { type: 'perf', pattern: /\b(perf|performance|optimize|speed)\b/, label: 'performance' },
    { type: 'build', pattern: /\b(build|compile|dependency|dependencies|deps)\b/, label: 'build' },
    { type: 'ci', pattern: /\b(ci|workflow|action|pipeline)\b/, label: 'CI' },
    { type: 'revert', pattern: /\b(revert|reverts|reverting|rollback|undo)\b/, label: 'revert' },
    { type: 'feat', pattern: /\b(add|adds|added|feature|features|new|implement|implements|implemented|introduce|introduced)\b/, label: 'feature' }
  ];

  // Check each pattern in priority order
  for (const { type, pattern, label } of typePatterns) {
    if (lowerTitle.match(pattern)) {
      console.log(`[Bot] Detected ${label} keywords → suggesting "${type}"`);
      return type;
    }
  }

  console.log('[Bot] No specific keywords matched → suggesting "chore"');
  return 'chore';
}

/**
 * Generate the header section of the bot message
 * @param {string} safeTitle - Current PR title (markdown-escaped)
 * @param {string} suggestedType - Suggested conventional type
 * @returns {string} Formatted header
 */
function generateMessageHeader(safeTitle, suggestedType) {
  return `${COMMENT_IDENTIFIER}
## PR Title Needs Conventional Format

**Your current title is:**
\`\`\`
${safeTitle}
\`\`\`

**It needs to have a type prefix like:**
\`\`\`
${suggestedType}: ${safeTitle}
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
2. Click the **edit button** (✏️) next to the PR title at the top of the page
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
 * Escape user-provided text for safe markdown display
 * Prevents markdown injection without altering meaning
 * @param {string} text
 * @returns {string}
 */
function escapeForMarkdown(text) {
  return text
    .replace(/```/g, "'''")
    .replace(/\r?\n|\r/g, ' ')
    .trim();
}

/**
 * Compose the complete bot message
 * @param {Object} params - Message parameters
 * @param {string} params.safeTitle - Markdown-escaped title
 * @param {string} params.escapedTitle - Shell-escaped title
 * @param {string} params.suggestedType - Suggested conventional type
 * @param {number} params.prNumber - PR number
 * @returns {string} Complete formatted message
 */
function composeBotMessage({ safeTitle, escapedTitle, suggestedType, prNumber }) {
  return (
    generateMessageHeader(safeTitle, suggestedType) +
    generateFixInstructions(suggestedType, escapedTitle, prNumber) +
    generateValidTypesList()
  );
}

/**
 * Format the bot comment message with title guidance
 * @param {string} currentTitle - The current PR title
 * @param {string} suggestedType - The suggested conventional type
 * @param {number} prNumber - The PR number
 * @returns {string} Formatted markdown message
 */
function formatMessage(currentTitle, suggestedType, prNumber) {
  // Escape shell-sensitive characters for the CLI example
  const escapedTitle = currentTitle.replace(/["$`\\]/g, '\\$&');
  const safeTitle = escapeForMarkdown(currentTitle);

  return composeBotMessage({
    safeTitle,
    escapedTitle,
    suggestedType,
    prNumber,
  });
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

    // Skip if title already follows conventional commit format
    const conventionalRegex = /^(feat|fix|docs|style|refactor|test|build|ci|chore|revert)(\(.+\))?: .+/;
    if (conventionalRegex.test(prTitle)) {
      console.log("[Bot] ✅ Title already follows conventional commit format, skipping comment");
      return;
    }

    // Suggest appropriate conventional type
    const suggestedType = suggestConventionalType(prTitle);

    // Format the bot message
    const message = formatMessage(prTitle, suggestedType, prNumber);

    console.log('[Bot] Fetching PR comments with pagination...');

    // Fetch comments with pagination and early exit
    let commentCount = 0;
    let page = 1;
    let botComment = null;

    while (commentCount < MAX_COMMENTS_TO_FETCH && !botComment) {
      const response = await github.rest.issues.listComments({
        owner: context.repo.owner,
        repo: context.repo.repo,
        issue_number: prNumber,
        per_page: 100,
        page: page
      });

      commentCount += response.data.length;

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

    console.log(`[Bot] Fetched ${commentCount} comments across ${page} page(s)`);

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