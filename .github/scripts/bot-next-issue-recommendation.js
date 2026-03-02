const SUPPORTED_GFI_REPOS = [
  'hiero-sdk-cpp',
  'hiero-sdk-swift',
  'hiero-sdk-python',
  'hiero-website',
  'hiero-sdk-js',
];

module.exports = async ({ github, context, core }) => {
  const { payload } = context;

  // Get PR information from automatic pull_request_target trigger
  let prNumber = payload.pull_request?.number;
  let prBody = payload.pull_request?.body || '';

  // Manual workflow_dispatch is no longer supported - inputs were removed
  // Only automatic triggers from merged PRs will work
  const repoOwner = context.repo.owner;
  const repoName = context.repo.repo;

  if (!prNumber) {
    core.info('No PR number found, skipping');
    return;
  }

  core.info(`Processing PR #${prNumber}`);

  // Parse PR body to find linked issues
  const MAX_PR_BODY_LENGTH = 50000; // Reasonable limit for PR body
  if (prBody.length > MAX_PR_BODY_LENGTH) {
    core.warning(`PR body exceeds ${MAX_PR_BODY_LENGTH} characters, truncating for parsing`);
    prBody = prBody.substring(0, MAX_PR_BODY_LENGTH);
  }
  const issueRegex = /(fixes|closes|resolves|fix|close|resolve)\s+(?:[\w-]+\/[\w-]+)?#(\d+)/gi;
  const matches = [...prBody.matchAll(issueRegex)];

  if (matches.length === 0) {
    core.info('No linked issues found in PR body');
    return;
  }

  // Get the first linked issue number
  const issueNumber = parseInt(matches[0][2]);
  core.info(`Found linked issue #${issueNumber}`);

  try {
    // Fetch issue details
    const { data: issue } = await github.rest.issues.get({
      owner: repoOwner,
      repo: repoName,
      issue_number: issueNumber,
    });

    // Normalize and check issue labels (case-insensitive)
    const labelNames = issue.labels.map(label => label.name.toLowerCase());
    const labelSet = new Set(labelNames);
    core.info(`Issue labels: ${labelNames.join(', ')}`);

    // Determine issue difficulty level
    const difficultyLevels = {
      beginner: labelSet.has('beginner'),
      goodFirstIssue: labelSet.has('good first issue'),
      intermediate: labelSet.has('intermediate'),
      advanced: labelSet.has('advanced'),
    };

    // Skip if intermediate or advanced
    if (difficultyLevels.intermediate || difficultyLevels.advanced) {
      core.info('Issue is intermediate or advanced level, skipping recommendation');
      return;
    }

    // Only proceed for Good First Issue or beginner issues
    if (!difficultyLevels.goodFirstIssue && !difficultyLevels.beginner) {
      core.info('Issue is not a Good First Issue or beginner issue, skipping');
      return;
    }

    let recommendedIssues = [];
    let recommendedLabel = null;
    let isFallback = false;

    recommendedIssues = await searchIssues(github, core, repoOwner, repoName, 'beginner');
    recommendedLabel = 'Beginner';

    if (recommendedIssues.length === 0) {
      isFallback = true;
      recommendedIssues = await searchIssues(github, core, repoOwner, repoName, 'good first issue');
      recommendedLabel = 'Good First Issue';
    }


    // Remove the issue they just solved
    recommendedIssues = recommendedIssues.filter(i => i.number !== issueNumber);

    // Generate and post comment
    const completedLabel = difficultyLevels.goodFirstIssue ? 'Good First Issue' : 'Beginner';
    const completedLabelText = completedLabel === 'Beginner' ? 'Beginner issue' : completedLabel;
    const recommendationMeta = {
      completedLabelText,
      recommendedLabel,
      isFallback,
    };
    await generateAndPostComment(github, context, core, prNumber, recommendedIssues, recommendationMeta);

  } catch (error) {
    core.setFailed(`Error processing issue #${issueNumber}: ${error.message}`);
  }
};

async function searchIssues(github, core, owner, repo, label) {
  try {
    const query = `repo:${owner}/${repo} type:issue state:open label:"${label}" no:assignee`;
    core.info(`Searching for issues with query: ${query}`);

    const { data: searchResult } = await github.rest.search.issuesAndPullRequests({
      q: query,
      per_page: 6,
    });

    core.info(`Found ${searchResult.items.length} issues with label "${label}"`);
    return searchResult.items;
  } catch (error) {
    core.warning(`Error searching for issues with label "${label}": ${error.message}`);
    return [];
  }
}

async function generateAndPostComment(github, context, core, prNumber, recommendedIssues, { completedLabelText, recommendedLabel, isFallback }) {
  const marker = '<!-- next-issue-bot-marker -->';

  // Build comment content
  let comment = `${marker}\n\n🎉 **Nice work completing a ${completedLabelText}!**\n\n`;
  comment += `Thank you for your contribution to the Hiero Python SDK! We're excited to have you as part of our community.\n\n`;

  if (recommendedIssues.length > 0) {

    if (isFallback) {
      comment += `Here are some **${recommendedLabel}** issues at a similar level you might be interested in working on next:\n\n`;
    } else {
      comment += `Here are some issues labeled **${recommendedLabel}** you might be interested in working on next:\n\n`;
    }

    // Sanitize title: escape markdown link syntax and special characters
    const sanitizeTitle = (title) => title
      .replace(/\[/g, '\\[')
      .replace(/\]/g, '\\]')
      .replace(/\(/g, '\\(')
      .replace(/\)/g, '\\)');

    recommendedIssues.slice(0, 5).forEach((issue, index) => {
      comment += `${index + 1}. [${sanitizeTitle(issue.title)}](${issue.html_url})\n`;
      if (issue.body && issue.body.length > 0) {
        const description = extractIssueDescription(issue.body);
        comment += `   ${description}\n\n`;
      } else {
        comment += `   *No description available*\n\n`;
      }
    });
  } else {
    comment += `There are currently no open issues available at or near the ${completedLabelText} level in this repository.\n\n`;
    comment += `You can check out **Good First Issues** in other Hiero repositories:\n\n`;
    const repoQuery = SUPPORTED_GFI_REPOS
      .map(repo => `repo:${context.repo.owner}/${repo}`)
      .join(' OR ');

    const gfiSearchQuery = [
      'is:open',
      'is:issue',
      `org:${context.repo.owner}`,
      'archived:false',
      'no:assignee',
      '(label:"good first issue" OR label:"skill: good first issue")',
      `(${repoQuery})`,
    ].join(' ');

    const gfiQuery = `https://github.com/issues?q=${encodeURIComponent(gfiSearchQuery)}`;

    comment += `[View Good First Issues across supported Hiero repositories](${gfiQuery})\n\n`;
  }

  comment += `🌟 **Stay connected with the project:**\n`;
  comment += `- ⭐ [Star this repository](https://github.com/${context.repo.owner}/${context.repo.repo}) to show your support\n`;
  comment += `- 👀 [Watch this repository](https://github.com/${context.repo.owner}/${context.repo.repo}/watchers) to get notified of new issues and releases\n\n`;

  comment += `We look forward to seeing more contributions from you! If you have any questions, feel free to ask in our [Discord community](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/discord.md).\n\n`;
  comment += `From the Hiero Python SDK Team 🚀`;

  // Check for existing comment
  try {
    const { data: comments } = await github.rest.issues.listComments({
      owner: context.repo.owner,
      repo: context.repo.repo,
      issue_number: prNumber,
    });

    const existingComment = comments.find(c => c.body.includes(marker));

    if (existingComment) {
      core.info('Comment already exists, skipping');
      return;
    }
  } catch (error) {
    core.warning(`Error checking existing comments: ${error.message}`);
  }

  // Post the comment
  try {
    await github.rest.issues.createComment({
      owner: context.repo.owner,
      repo: context.repo.repo,
      issue_number: prNumber,
      body: comment,
    });

    core.info(`Successfully posted comment to PR #${prNumber}`);
  } catch (error) {
    core.setFailed(`Error posting comment: ${error.message}`);
  }
}
function extractIssueDescription(body) {
  if (!body) return '*No description available*';

  // Guard against massive inputs blocking the regex event loop
  const safeBody = body.length > 50000 ? body.substring(0, 50000) : body;

  // Try to find the specific description section first
  const sectionRegex = /^##*\s*👾\s*(Description of the issue|Issue description)[^\r\n]*\r?\n([\s\S]*?)(?=^#|$(?![\s\S]))/im;
  const match = safeBody.match(sectionRegex);

  let targetText = safeBody;
  if (match) {
    if (match[2] && match[2].trim()) {
      targetText = match[2];
    } else {
      return '*No description available*';
    }
  }

  // Sanitize: strip HTML, normalize whitespace, escape markdown formatting (links, emphasis, bold)
  const sanitized = targetText
    .replace(/<[^>]*>/g, '') // Remove HTML tags
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1') // Remove markdown links, keep text
    .replace(/(\*\*|__)(.*?)\1/g, '$2') // Remove bold
    .replace(/(\*|_)(.*?)\1/g, '$2') // Remove italics
    .replace(/(`{1,3})(.*?)\1/g, '$2') // Remove inline code and codeblocks
    .replace(/#{1,6}\s?/g, '') // Remove headings
    .replace(/>/g, '') // Remove blockquotes
    .replace(/\|/g, '') // Remove table pipes
    .replace(/\s+/g, ' ') // Normalize whitespace
    .trim();

  // If we couldn't find a meaningful description, return a default
  if (!sanitized) {
    return '*No description available*';
  }

  // Truncate to 150 characters
  if (sanitized.length > 150) {
    return sanitized.substring(0, 150) + '...';
  }

  return sanitized;
}

module.exports.extractIssueDescription = extractIssueDescription;
