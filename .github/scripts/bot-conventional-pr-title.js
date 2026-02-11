// .github/scripts/bot-conventional-pr-title.js

const BOT_SIGNATURE = '<!-- bot-conventional-pr-title -->';

module.exports = async ({ github, context, core }) => {
  const { owner, repo } = context.repo;

  // Validate event context
  if (!context.payload.pull_request) {
    console.log('No pull_request in context, skipping');
    return;
  }

  const prNumber = context.payload.pull_request.number;
  const prTitle = context.payload.pull_request.title;

  console.log(`[Bot] PR #${prNumber}: ${prTitle}`);

  // Check for dry-run mode
  const dryRun = process.env.DRY_RUN === 'true';
  if (dryRun) {
    console.log('[Bot] DRY RUN MODE - No changes will be made');
  }

  // Suggest conventional type based on title keywords
  function suggestConventionalType(title) {
    const lower = title.toLowerCase();
    
    if (lower.match(/\b(format|formatting|style|prettier|eslint|lint)\b/)) return 'style';
    if (lower.match(/\b(docs|documentation|readme|comment)\b/)) return 'docs';
    if (lower.match(/\b(fix|bug|issue|error|crash|problem)\b/)) return 'fix';
    if (lower.match(/\b(test|testing|spec|unit|integration)\b/)) return 'test';
    if (lower.match(/\b(refactor|refactoring|restructure)\b/)) return 'refactor';
    if (lower.match(/\b(perf|performance|optimize|speed)\b/)) return 'perf';
    if (lower.match(/\b(build|compile|dependency|dependencies|deps)\b/)) return 'build';
    if (lower.match(/\b(ci|workflow|action|pipeline)\b/)) return 'ci';
    if (lower.match(/\b(add|feature|new|implement|introduce)\b/)) return 'feat';
    
    return 'chore';
  }

  const suggestedType = suggestConventionalType(prTitle);
  console.log(`[Bot] Suggested type: ${suggestedType}`);

  // Build comment message
  const escapedTitle = prTitle.replace(/[`$\\]/g, '\\$&').replace(/\r?\n|\r/g, ' ').trim();
  const safeTitle = prTitle.replace(/\r?\n|\r/g, ' ').trim();
  
  const message = `${BOT_SIGNATURE}
## ⚠️ PR Title Needs Conventional Format

**Your current title:**
\`\`\`
${safeTitle}
\`\`\`

**It needs a type prefix like:**
\`\`\`
${suggestedType}: ${safeTitle}
\`\`\`

---

### How to Fix This

#### Option 1: Via GitHub UI
1. Go to the top of this PR page
2. Click on the title to edit it
3. Add the type prefix (e.g., \`${suggestedType}:\`) before your current title
4. Save the changes

#### Option 2: Via Command Line
\`\`\`bash
gh pr edit ${prNumber} --title "${suggestedType}: ${escapedTitle}"
\`\`\`

---

### Valid Conventional Commit Types
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

---
*From the Hiero Python SDK Team*`;

  // Check for existing bot comment
  const { data: comments } = await github.rest.issues.listComments({
    owner,
    repo,
    issue_number: prNumber,
  });

  const existingComment = comments.find(c => c.body && c.body.includes(BOT_SIGNATURE));

  if (dryRun) {
    console.log(`[Bot] Would ${existingComment ? 'UPDATE' : 'CREATE'} comment`);
    return;
  }

  if (existingComment) {
    console.log(`[Bot] Updating existing comment #${existingComment.id}`);
    await github.rest.issues.updateComment({
      owner,
      repo,
      comment_id: existingComment.id,
      body: message,
    });
    console.log('[Bot] ✅ Comment updated successfully');
  } else {
    console.log('[Bot] Creating new comment');
    await github.rest.issues.createComment({
      owner,
      repo,
      issue_number: prNumber,
      body: message,
    });
    console.log('[Bot] ✅ Comment created successfully');
  }
};
