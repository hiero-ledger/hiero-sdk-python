/**
 * Ordered list of difficulty levels from easiest → hardest.
 * Used for progression logic.
 */
const LEVEL_ORDER = [
  "good first issue",
  "beginner",
  "intermediate",
  "advanced"
];

/**
 * Maps difficulty levels to possible label aliases.
 * Supports both standard and "skill:" prefixed labels.
 */
const LEVEL_LABEL_ALIASES = {
  "good first issue": [
    "good first issue",
    "skill: good first issue"
  ],
  "beginner": [
    "beginner",
    "skill: beginner"
  ],
  "intermediate": [
    "intermediate",
    "skill: intermediate"
  ],
  "advanced": [
    "advanced",
    "skill: advanced"
  ]
};

/**
 * Configuration for each difficulty level.
 * - display: human-readable label
 * - required: minimum completed issues needed to unlock next level
 */
const LEVEL_CONFIG = {
  "good first issue": {
    display: "Good First Issue",
    required: 0
  },
  beginner: {
    display: "Beginner",
    required: 1
  },
  intermediate: {
    display: "Intermediate",
    required: 1
  },
  advanced: {
    display: "Advanced",
    required: 1
  }
};

/**
 * Fetch all supported repositories in an organization.
 * Filters out archived repos and forks.
 *
 * @param {object} github - GitHub API client
 * @param {object} core - GitHub Actions core
 * @param {string} owner - Organization name
 * @returns {Promise<string[]>} List of repository names
 */
async function getSupportedRepos(github, core, owner) {
  try {
    const repos = [];

    for await (const response of github.paginate.iterator(
      github.rest.repos.listForOrg,
      {
        org: owner,
        per_page: 100
      }
    )) {
      for (const repo of response.data) {
        if (repo.archived) continue; // Skip archived repos
        if (repo.fork) continue; // Skip forks

        repos.push(repo.name);
      }
    }

    core.debug(`Discovered repositories: ${repos.join(", ")}`);
    return repos;

  } catch (error) {
    core.warning(`Failed to fetch repositories: ${error.message}`);
    return [];
  }
}

/**
 * Computes how many issues a user has completed at each difficulty level.
 *
 * @param {object} github
 * @param {object} core
 * @param {string} owner
 * @param {string} username
 * @returns {Promise<Object>} Progress per difficulty level
 */
async function getUserLevelProgress(github, core, owner, username) {
  const progress = {
    "good first issue": 0,
    beginner: 0,
    intermediate: 0,
    advanced: 0
  };

  try {
    const query = `is:pr is:merged author:${username} org:${owner}`;
    
    const { data } = await github.rest.search.issuesAndPullRequests({
      q: query,
      per_page: 50
    });

    for (const pr of data.items) {
      const labels = (pr.labels || []).map(l => l.name.toLowerCase());

      for (const level of LEVEL_ORDER) {
        const aliases = LEVEL_LABEL_ALIASES[level] || [level];
        if (aliases.some(a => labels.includes(a))) {
          progress[level]++;
          break;
        }
      }
    }

  } catch (error) {
    core.warning(`Unable to compute contribution progress: ${error.message}`);
  }

  return progress;
}

/**
 * Fetches candidate issues using a prioritized, sequential fallback strategy.
 * Stops at the first non-empty result set.
 *
 * Priority order:
 * 1. Next level (current repository)
 * 2. Same level (current repository)
 * 3. Next level (other repositories)
 * 4. Same level (other repositories)
 * 5. Previous level (fallback)
 *
 * @returns {Promise<Array<Object>>} List of recommended issues
 */
async function gatherCandidateIssues(
  github,
  core,
  owner,
  repoName,
  otherRepos,
  completedLevel,
  nextLevel,
  prevLevel
) {
  const strategies = [
    // Next level in current repo
    nextLevel && { repos: [repoName], level: nextLevel },

    // Same level in current repo
    { repos: [repoName], level: completedLevel },

    // Next level in other repos
    nextLevel && { repos: otherRepos, level: nextLevel },

    // Same level in other repos
    { repos: otherRepos, level: completedLevel },

    // Previous level fallback (only used if no higher/same level issues found)
    prevLevel && { repos: [repoName], level: prevLevel },
    prevLevel && { repos: otherRepos, level: prevLevel }
  ].filter(Boolean);

  for (const { repos, level } of strategies) {
    const issues = await searchIssues(github, core, owner, repos, level);
    if (issues.length > 0) return issues;
  }

  return [];
}

/**
 * Get previous difficulty level.
 * @param {string} level
 * @returns {string|null}
 */
function getPreviousLevel(level) {
  const index = LEVEL_ORDER.indexOf(level);
  return index > 0 ? LEVEL_ORDER[index - 1] : null;
}

/**
 * Get next difficulty level.
 * @param {string} level
 * @returns {string|null}
 */
function getNextLevel(level) {
  const index = LEVEL_ORDER.indexOf(level);
  return index >= 0 && index < LEVEL_ORDER.length - 1
    ? LEVEL_ORDER[index + 1]
    : null;
}

/**
 * Main GitHub Action entry point.
 * Processes a PR, determines completed issue level,
 * and posts recommended issues.
 */
module.exports = async ({ github, context, core }) => {
  const { payload } = context;

  let prNumber = payload.pull_request?.number;
  let prBody = payload.pull_request?.body || '';

  const repoOwner = context.repo.owner;
  const repoName = context.repo.repo;

  if (!prNumber) {
    core.info('No PR number found, skipping');
    return;
  }

  core.info(`Processing PR #${prNumber}`);

   // Extract linked issue number(s) from PR body
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

  const issueNumber = Number(matches[0][2]);
  const referencedIssues = [issueNumber];
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

    core.info(`Issue labels: ${labelNames.join(", ")}`);

    const completedLevel = LEVEL_ORDER.find(level => {
      const aliases = LEVEL_LABEL_ALIASES[level] || [level];
      return aliases.some(alias => labelSet.has(alias));
    });

    const username = context.payload.pull_request.user.login;

    const userProgress = await getUserLevelProgress(
      github,
      core,
      repoOwner,
      username
    );

    core.info(`User contribution progress: ${JSON.stringify(userProgress)}`);

    if (!completedLevel) {
      core.info("Issue does not match known difficulty levels");
      return;
    }

    core.info(`Completed level: ${completedLevel}`);

    let recommendedIssues = [];
    let usedLevel = completedLevel;
    let recommendedLabel = LEVEL_CONFIG[completedLevel].display;
    let isFallback = false;

    const LIMIT = 5;
    let nextLevel = getNextLevel(completedLevel);

    // Gate progression
    if (nextLevel) {
      const required = LEVEL_CONFIG[nextLevel].required;

      if (userProgress[completedLevel] < required) {
        core.info(`User not eligible for ${nextLevel} yet`);
        nextLevel = null;
      }
    }
    const prevLevel = getPreviousLevel(completedLevel);

    // Fetch repos
    let allRepos = await getSupportedRepos(github, core, repoOwner);
    if (allRepos.length === 0) {
      core.warning("Using fallback repo list");
      allRepos = [
        "hiero-sdk-cpp",
        "hiero-sdk-swift",
        "hiero-sdk-python",
        "hiero-website",
        "hiero-sdk-js"
      ];
    }

    const otherRepos = allRepos.filter(r => r !== repoName);

    // Fetch candidate issues
    const candidates = await gatherCandidateIssues(
      github,
      core,
      repoOwner,
      repoName,
      otherRepos,
      completedLevel,
      nextLevel,
      prevLevel
    );

    for (const candidate of candidates) {

      if (referencedIssues.includes(candidate.number)) continue;

      // avoid duplicates
      if (!recommendedIssues.find(i => i.html_url === candidate.html_url)) {
        recommendedIssues.push(candidate);
      }

      if (recommendedIssues.length === LIMIT) break;
    }

    if (recommendedIssues.length > 0) {
      const first = recommendedIssues[0];

      const labels = (first.labels || []).map(l => l.name.toLowerCase());

      const detectedLevel = LEVEL_ORDER.find(level =>
        (LEVEL_LABEL_ALIASES[level] || [level]).some(alias =>
          labels.includes(alias)
        )
      );

      usedLevel = detectedLevel || completedLevel;

      recommendedLabel = LEVEL_CONFIG[usedLevel].display;
    }

    isFallback = usedLevel === prevLevel;

    const completedLabelText = LEVEL_CONFIG[completedLevel].display;

    const recommendationMeta = {
      completedLabelText,
      recommendedLabel,
      isFallback,
    };

    await generateAndPostComment(
      github,
      context,
      core,
      prNumber,
      recommendedIssues,
      recommendationMeta,
      allRepos
    );
  } catch (error) {
    core.setFailed(`Error processing issue #${issueNumber}: ${error.message}`);
  }
};

async function searchIssues(github, core, owner, repos, level) {
  try {

    const labels = LEVEL_LABEL_ALIASES[level] || [level];

    const labelQuery = labels
      .map(l => `label:"${l}"`)
      .join(" OR ");

    const repoFilter = repos && repos.length > 0
      ? repos.map(r => `repo:${owner}/${r}`).join(" OR ")
      : `org:${owner}`;

    const query = [
      "is:issue",
      "is:open",
      "no:assignee",
      `(${labelQuery})`,
      `(${repoFilter})`
    ].join(" ");

    core.debug(`Searching issues with query: ${query}`);

    const { data: result } = await github.rest.search.issuesAndPullRequests({
      q: query,
      per_page: 6,
    });

    core.debug(`Found ${result.items.length} issues`);

    return result.items;

  } catch (error) {
    core.warning(`Search error: ${error.message}`);
    return [];
  }
}

async function generateAndPostComment(github, context, core, prNumber, recommendedIssues, { completedLabelText, recommendedLabel, isFallback }, allRepos) {
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

    recommendedIssues.slice(0, 5).forEach((recIssue, index) => {
      comment += `${index + 1}. [${sanitizeTitle(recIssue.title)}](${recIssue.html_url})\n`;
      if (recIssue.body && recIssue.body.length > 0) {
        const description = extractIssueDescription(recIssue.body);
        comment += `   ${description}\n\n`;
      } else {
        comment += `   *No description available*\n\n`;
      }
    });
  } else {
    comment += `There are currently no open issues available at or near the ${completedLabelText} level in this repository.\n\n`;
    comment += `You can check out **Good First Issues** in other Hiero repositories:\n\n`;
    const repoQuery = allRepos
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
