// ---------------------------------------------------------------------------
// Comment builder
// ---------------------------------------------------------------------------

const { CONFIG } = require('../config');

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
    .replace(/\\/g, '\\\\')
    .replace(/\[/g, '\\[')
    .replace(/\]/g, '\\]')
    .replace(/\(/g, '\\(')
    .replace(/\)/g, '\\)')
    .replace(/`/g, '\\`')
    .replace(/\*/g, '\\*')
    .replace(/_/g, '\\_')
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

module.exports = {
  buildIssueListBlock,
  buildMilestoneBlock,
  buildRecommendationComment,
};
