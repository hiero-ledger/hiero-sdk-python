/**
 * Bot script to comment on PRs with invalid conventional commit titles
 * Triggers when pr-check-title.yml workflow fails
 * Provides helpful guidance on fixing the PR title
 */

const CONVENTIONAL_TYPES = [
  'feat', 'fix', 'docs', 'style', 'refactor',
  'test', 'chore', 'ci', 'perf', 'build', 'revert'
];

const COMMENT_IDENTIFIER = '<!-- conventional-pr-title-bot -->';

// Keyword mappings for type suggestions (order matters - most specific first)
const TYPE_KEYWORDS = [
  { keywords: ['format', 'style', 'lint'], type: 'style' },
  { keywords: ['doc', 'readme'], type: 'docs' },
  { keywords: ['fix', 'bug', 'error'], type: 'fix' },
  { keywords: ['test'], type: 'test' },
  { keywords: ['refactor'], type: 'refactor' },
  { keywords: ['ci', 'workflow', 'action'], type: 'ci' },
  { keywords: ['chore', 'update', 'upgrade'], type: 'chore' },
  { keywords: ['perf', 'performance', 'optimize'], type: 'perf' },
  { keywords: ['build', 'deps', 'dependencies'], type: 'build' },
];

/**
 * Suggests an appropriate conventional commit type based on PR title keywords
 */
function suggestConventionalType(title) {
  const lowerTitle = title.toLowerCase();
  
  // Find first matching type based on keywords
  for (const { keywords, type } of TYPE_KEYWORDS) {
    if (keywords.some(keyword => lowerTitle.includes(keyword))) {
      return type;
    }
  }
  
  // Default to feat for new functionality
  return 'feat';
}

/**
 * Formats the bot comment message with helpful instructions
 */
function formatMessage(currentTitle, suggestedType, prNumber) {
  return `${COMMENT_IDENTIFIER}
## ⚠️ PR Title Needs Conventional Format

**Your current title is:**
\`\`\`
${currentTitle}
\`\`\`

**It needs to have a type prefix like:**
\`\`\`
${suggestedType}: ${currentTitle}
\`\`\`

---

### 📝 How to Change the PR Title on GitHub

**Option 1: GitHub UI**
1. Go to your PR page (you should already be there)
2. Look at the top where the title is displayed
3. Click the **"Edit"** button next to the PR title (it's a small button to the right of the title)
4. Update the title to include the type prefix
5. Click **"Save"**

**Option 2: GitHub CLI**
\`\`\`bash
gh pr edit ${prNumber} --title "${suggestedType}: ${currentTitle}"
\`\`\`

---

### 📚 Valid Conventional Commit Types

- \`feat\`: A new feature
- \`fix\`: A bug fix
- \`docs\`: Documentation only changes
- \`style\`: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
- \`refactor\`: A code change that neither fixes a bug nor adds a feature
- \`test\`: Adding missing tests or correcting existing tests
- \`chore\`: Changes to the build process or auxiliary tools and libraries
- \`ci\`: Changes to our CI configuration files and scripts
- \`perf\`: A code change that improves performance
- \`build\`: Changes that affect the build system or external dependencies

**Read about conventional commit messages here:** [Conventional Commits](https://www.conventionalcommits.org/)

---

*This comment will be automatically updated if the PR title changes.*`;
}

/**
 * Main function - runs the bot logic
 */
async function run() {
  const github = require('@actions/github');
  const core = require('@actions/core');

  try {
    const token = core.getInput('github-token', { required: true });
    const prNumber = parseInt(core.getInput('pr-number', { required: true }));
    const prTitle = core.getInput('pr-title', { required: true });

    const octokit = github.getOctokit(token);
    const context = github.context;

    core.info(`Processing PR #${prNumber} with title: "${prTitle}"`);

    // Find existing bot comment to avoid duplicates
    const { data: comments } = await octokit.rest.issues.listComments({
      owner: context.repo.owner,
      repo: context.repo.repo,
      issue_number: prNumber,
    });

    const botComment = comments.find(comment =>
      comment.body && comment.body.includes(COMMENT_IDENTIFIER)
    );

    // Suggest appropriate type based on title
    const suggestedType = suggestConventionalType(prTitle);
    core.info(`Suggested type: ${suggestedType}`);

    // Format the helpful message
    const message = formatMessage(prTitle, suggestedType, prNumber);

    if (botComment) {
      // Update existing comment to avoid spam
      await octokit.rest.issues.updateComment({
        owner: context.repo.owner,
        repo: context.repo.repo,
        comment_id: botComment.id,
        body: message,
      });
      core.info(`✅ Updated existing comment ID: ${botComment.id}`);
    } else {
      // Create new comment
      const { data: newComment } = await octokit.rest.issues.createComment({
        owner: context.repo.owner,
        repo: context.repo.repo,
        issue_number: prNumber,
        body: message,
      });
      core.info(`✅ Created new comment ID: ${newComment.id}`);
    }

    core.info('Bot completed successfully!');
  } catch (error) {
    core.setFailed(`Bot failed: ${error.message}`);
    throw error;
  }
}

// Export for testing and direct execution
module.exports = { run, suggestConventionalType, formatMessage };

// Run if called directly
if (require.main === module) {
  run();
}
