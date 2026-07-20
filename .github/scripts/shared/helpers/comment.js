// ---------------------------------------------------------------------------
// Comment builder
// ---------------------------------------------------------------------------

const { CONFIG } = require('../config');

const MARKDOWN_ESCAPE_REGEX = /[[\]()`*_\\]/g;

/**
 * Escapes user-controlled issue titles before inserting them into Markdown.
 *
 * Prevents broken formatting and accidental mentions in bot comments.
 *
 * @param {string} text
 * @returns {string}
 */
function escapeMarkdownText(text) {
  return String(text)
    .replace(MARKDOWN_ESCAPE_REGEX, '\\$&')
    .replace(/@/g, '@\u200B');
}

function buildIssueListBlock(issues = []) {
  if (issues.length > 0) {
    return [
      'Here are some issues you might want to explore next:',
      '',
      ...issues.map(i => {
        const rawTitle = i?.title ?? 'Untitled issue';
        const title = escapeMarkdownText(rawTitle);
        const url   = i?.html_url ?? '#';
        return `- [${title}](${url})`;
      }),
      '',
    ];
  }
  return ['No suitable issues are available right now — check back soon!', ''];
}

/**
 * Builds a milestone banner if a new level was unlocked.
 *
 * @param {string|null} unlockedLevelKey
 * @returns {string[]} Lines to include in the comment.
 */
function buildMilestoneBlock(unlockedLevelKey) {
  const displayName = unlockedLevelKey
    ? CONFIG.skillPrerequisites[unlockedLevelKey]?.displayName
    : null;

  return displayName
    ? [`🏆 **Milestone unlocked: you've reached ${displayName} level!** 🎉`, '']
    : [];
}

/**
 * Builds the full GitHub PR comment for issue recommendations.
 *
 * Structure:
 *   - HTML marker (used by alreadyCommented to detect duplicates)
 *   - Greeting and completion acknowledgment
 *   - Optional milestone unlock banner
 *   - Issue list (or "no issues" fallback)
 *   - Stay-connected footer
 *
 * @param {string}      username             - GitHub login of the contributor.
 * @param {Array}       issues               - Recommended issues (may be empty).
 * @param {string}      completedDisplayName - Human-readable name of the completed level.
 * @param {string|null} unlockedLevelKey     - Canonical key of newly unlocked level, or null.
 * @returns {string} Fully rendered comment body.
 */
function buildRecommendationComment(username, issues, completedDisplayName, unlockedLevelKey = null) {
  const homeRepo = CONFIG.repos.find(r => r.isHome) || {};

  const {
    repositoryUrl: repoUrl = '',
    communityLinks = {},
    botSignature = 'Hiero Team',
  } = homeRepo;

  const hasRepoUrl = Boolean(repoUrl);

  return [
    CONFIG.commentMarker,
    '',
    `👋 Hi @${username}! Great work completing a **${completedDisplayName}** issue! 🎉`,
    '',
    'Thanks for your contribution! 🚀',
    '',
    ...buildMilestoneBlock(unlockedLevelKey),
    ...buildIssueListBlock(issues),
    ...(hasRepoUrl ? [
    '🌟 **Stay connected:**',
    `- ⭐ [Star this repository](${repoUrl})`,
    `- 👀 [Watch for new issues](${repoUrl}/watchers)`,
    ...(communityLinks?.discord
      ? [`- 💬 [Join us on Discord](${communityLinks.discord})`]
      : []),
    ] : []),

    '',
    'Happy coding! 🚀',
    `_— ${botSignature}_`,
  ].join('\n');
}

function buildReminderComment(commenter) {
  return `👋 Hi @${commenter}! If you'd like to work on this issue, please comment \`/assign\` to get assigned.`;
}

function getCurrentAssigneeMention(issue) {
  const login = issue?.assignees?.[0]?.login;
  return login ? `@${login}` : 'someone';
}

function unassignedIssuesUrl(owner, repo, label) {
  return `https://github.com/${owner}/${repo}/issues?q=${encodeURIComponent(
    `is:issue is:open label:"${label}" no:assignee`
  )}`;
}

function buildAlreadyAssignedComment(commenter, issue, { owner, repo, label }) {
  return `👋 Hi @${commenter}, thanks for your interest! This issue is already assigned to ${getCurrentAssigneeMention(
    issue
  )}, but we'd love your help on another one. You can find more "${label}" issues [here](${unassignedIssuesUrl(
    owner,
    repo,
    label
  )}).`;
}

function buildGuardComment(commenter, { owner, repo, prereqLabel, prereqDisplayName, requiredCount, currentDisplayName }) {
  const timesPhrase = requiredCount === 1 ? 'one' : requiredCount;
  const issuePhrase = requiredCount === 1 ? 'issue' : 'issues';
  return `👋 Hi @${commenter}! Thanks for your interest in contributing 💡\n\nBefore taking on a **${currentDisplayName}** issue, we ask contributors to complete at least ${timesPhrase} **${prereqDisplayName}** ${issuePhrase} first.\n\n👉 [Find one here](${unassignedIssuesUrl(
    owner,
    repo,
    prereqLabel
  )})\n\nOnce you've done that, come back — we'll be happy to assign this! 😊`;
}

function buildLimitComment(commenter, { maxAllowed, spamLimited }) {
  return spamLimited
    ? `Hi @${commenter}, you are limited to **${maxAllowed} active issue${maxAllowed === 1 ? '' : 's'}** at a time. Please complete your current assignment before requesting another.`
    : `👋 Hi @${commenter}, you already have **${maxAllowed} open assignment${maxAllowed === 1 ? '' : 's'}**. Please finish one before requesting another.`;
}

function buildSpamBlockedComment(commenter, { prereqDisplayName }) {
  return `Hi @${commenter}, your account is currently restricted to **${prereqDisplayName}** issues. Please complete one or contact a maintainer to have restrictions reviewed.`;
}

function reminderMarkerFor(levelKey) {
  return `<!-- assign-reminder:${levelKey} -->`;
}

function guardMarkerFor(levelKey) {
  return `<!-- assign-guard:${levelKey} -->`;
}


module.exports = {
  buildIssueListBlock,
  buildMilestoneBlock,
  buildRecommendationComment,
  buildAlreadyAssignedComment,
  buildGuardComment,
  buildLimitComment,
  buildReminderComment,
  buildSpamBlockedComment,
  reminderMarkerFor,
  guardMarkerFor,
};
