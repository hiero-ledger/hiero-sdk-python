/**
 * Bot script to provide guidance when PR titles don't follow conventional commit format
 * 
 * This bot:
 * - Detects when PR title validation fails
 * - Analyzes the title to suggest an appropriate conventional type
 * - Posts a helpful comment with instructions
 * - Updates existing comments instead of creating duplicates
 */

const COMMENT_IDENTIFIER = '<!-- conventional-pr-title-bot -->';

// Valid conventional commit types (ordered by priority for suggestion)
const CONVENTIONAL_TYPES = [
  'feat',     // New feature
  'fix',      // Bug fix
  'docs',     // Documentation changes
  'style',    // Code style changes (formatting, missing semi-colons, etc)
  'refactor', // Code refactoring
  'perf',     // Performance improvements
  'test',     // Adding or updating tests
  'build',    // Build system changes
  'ci',       // CI configuration changes
  'chore',    // Other changes that don't modify src or test files
  'revert',   // Reverts a previous commit
];

/**
 * Suggests an appropriate conventional type based on PR title keywords
 * @param {string} title - The PR title to analyze
 * @returns {string} - Suggested conventional commit type
 */
function suggestConventionalType(title) {
  console.log(`[Bot] Analyzing title for type suggestion: "${title}"`);
  
  const lowerTitle = title.toLowerCase();
  
  // Priority-based keyword matching
  if (lowerTitle.match(/\b(format|formatting|prettier|eslint|lint|style)\b/)) {
    console.log('[Bot] Detected formatting/style keywords → suggesting "style"');
    return 'style';
  }
  if (lowerTitle.match(/\b(doc|docs|documentation|readme|comment|guide)\b/)) {
    console.log('[Bot] Detected documentation keywords → suggesting "docs"');
    return 'docs';
  }
  if (lowerTitle.match(/\b(fix|bug|issue|error|crash|patch)\b/)) {
    console.log('[Bot] Detected fix keywords → suggesting "fix"');
    return 'fix';
  }
  if (lowerTitle.match(/\b(test|tests|testing|spec|unittest)\b/)) {
    console.log('[Bot] Detected test keywords → suggesting "test"');
    return 'test';
  }
  if (lowerTitle.match(/\b(refactor|restructure|reorganize|cleanup|clean up)\b/)) {
    console.log('[Bot] Detected refactor keywords → suggesting "refactor"');
    return 'refactor';
  }
  if (lowerTitle.match(/\b(ci|workflow|action|pipeline|build)\b/)) {
    console.log('[Bot] Detected CI keywords → suggesting "ci"');
    return 'ci';
  }
  if (lowerTitle.match(/\b(perf|performance|optimize|speed)\b/)) {
    console.log('[Bot] Detected performance keywords → suggesting "perf"');
    return 'perf';
  }
  if (lowerTitle.match(/\b(build|compile|dependency|dependencies|deps)\b/)) {
    console.log('[Bot] Detected build keywords → suggesting "build"');
    return 'build';
  }
  
  // Default to 'chore' for miscellaneous changes
  console.log('[Bot] No specific keywords matched → suggesting "chore" as default');
  return 'chore';
}

/**
 * Formats the bot message with guidance
 * @param {string} currentTitle - The current (invalid) PR title
 * @param {string} suggestedType - The suggested conventional type
 * @param {number} prNumber - The PR number
 * @returns {string} - Formatted markdown message
 */
function formatMessage(currentTitle, suggestedType, prNumber) {
  console.log(`[Bot] Formatting message for PR #${prNumber}`);
  console.log(`[Bot] Current title: "${currentTitle}"`);
  console.log(`[Bot] Suggested type: "${suggestedType}"`);
  
  return `${COMMENT_IDENTIFIER}

## 🤖 PR Title Needs Conventional Format

**Your current title is:**
\`\`\`
${currentTitle}
\`\`\`

**It needs to have a type prefix like:**
\`\`\`
${suggestedType}: ${currentTitle}
\`\`\`

---

### 📝 How to Fix This

#### Option 1: Via GitHub UI
1. Go to the top of this PR page
2. Click on the title to edit it
3. Add the type prefix (e.g., \`${suggestedType}:\`) before your current title
4. Save the changes

#### Option 2: Via Command Line
\`\`\`bash
gh pr edit ${prNumber} --title "${suggestedType}: ${currentTitle}"
\`\`\`

---

### ✅ Valid Types

Choose the type that best describes your changes:

- \`feat\` - A new feature
- \`fix\` - A bug fix
- \`docs\` - Documentation only changes
- \`style\` - Code style changes (formatting, missing semi-colons, etc)
- \`refactor\` - Code refactoring without changing functionality
- \`perf\` - Performance improvements
- \`test\` - Adding or updating tests
- \`build\` - Changes to build system or dependencies
- \`ci\` - CI/CD configuration changes
- \`chore\` - Other changes that don't modify src or test files
- \`revert\` - Reverts a previous commit

---

📚 **Learn more:** [Conventional Commits Specification](https://www.conventionalcommits.org/)

---

*This is an automated message. Once you update the title, this PR will be rechecked automatically.*`;
}

/**
 * Main bot execution function
 * @param {Object} params - Parameters from GitHub Actions
 * @param {Object} params.github - GitHub API client (octokit)
 * @param {Object} params.context - GitHub Actions context
 * @param {number} params.prNumber - PR number
 * @param {string} params.prTitle - Current PR title
 */
async function run({ github, context, prNumber, prTitle }) {
  try {
    console.log('='.repeat(60));
    console.log('[Bot] Starting conventional PR title bot');
    console.log('[Bot] PR Number:', prNumber);
    console.log('[Bot] PR Title:', prTitle);
    console.log('[Bot] Repository:', `${context.repo.owner}/${context.repo.repo}`);
    console.log('='.repeat(60));

    // Suggest appropriate conventional type
    const suggestedType = suggestConventionalType(prTitle);
    
    // Format the bot message
    const messageBody = formatMessage(prTitle, suggestedType, prNumber);
    
    console.log('[Bot] Fetching existing comments on PR #' + prNumber);
    
    // Fetch all comments with pagination support
    const comments = await github.paginate(github.rest.issues.listComments, {
      owner: context.repo.owner,
      repo: context.repo.repo,
      issue_number: prNumber,
    });
    
    console.log(`[Bot] Found ${comments.length} total comments on this PR`);

    // Look for existing bot comment
    const botComment = comments.find(comment =>
      comment.body && comment.body.includes(COMMENT_IDENTIFIER)
    );

    if (botComment) {
      console.log(`[Bot] Found existing bot comment (ID: ${botComment.id})`);
      console.log('[Bot] Updating existing comment instead of creating a new one');
      
      // Update existing comment
      await github.rest.issues.updateComment({
        owner: context.repo.owner,
        repo: context.repo.repo,
        comment_id: botComment.id,
        body: messageBody,
      });
      
      console.log('[Bot] ✅ Successfully updated existing comment');
    } else {
      console.log('[Bot] No existing bot comment found');
      console.log('[Bot] Creating new comment');
      
      // Create new comment
      const newComment = await github.rest.issues.createComment({
        owner: context.repo.owner,
        repo: context.repo.repo,
        issue_number: prNumber,
        body: messageBody,
      });
      
      console.log(`[Bot] ✅ Successfully created new comment (ID: ${newComment.data.id})`);
    }
    
    console.log('='.repeat(60));
    console.log('[Bot] Bot execution completed successfully');
    console.log('='.repeat(60));
    
  } catch (error) {
    console.error('='.repeat(60));
    console.error('[Bot] ❌ Error occurred during bot execution:');
    console.error('[Bot] Error name:', error.name);
    console.error('[Bot] Error message:', error.message);
    console.error('[Bot] Error stack:', error.stack);
    console.error('='.repeat(60));
    throw error;
  }
}

// Export functions for testing
module.exports = {
  run,
  suggestConventionalType,
  formatMessage,
};
