// ---------------------------------------------------------------------------
// Comment builder
// ---------------------------------------------------------------------------

const { CONFIG } = require('../config');

function buildIssueListBlock(issues) {
  if (issues.length > 0) {
    return [
      'Here are some issues you might want to explore next:',
      '',
      ...issues.map(i => `- [${i.title}](${i.html_url})`),
      '',
    ];
  }
  return ['No suitable issues are available right now — check back soon!', ''];
}

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
  return [
    CONFIG.commentMarker,
    '',
    `👋 Hi @${username}! Great work completing a **${completedDisplayName}** issue! 🎉`,
    '',
    'Thank you for your contribution to the Hiero Python SDK!',
    '',
    ...buildMilestoneBlock(unlockedLevelKey),
    ...buildIssueListBlock(issues),
    '🌟 **Stay connected:**',
    '- ⭐ [Star this repository](https://github.com/hiero-ledger/hiero-sdk-python)',
    '- 👀 [Watch for new issues](https://github.com/hiero-ledger/hiero-sdk-python/watchers)',
    '- 💬 [Join us on Discord](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/discord.md)',
    '',
    'Happy coding! 🚀',
    '_— Hiero Python SDK Team_',
  ].join('\n');
}

module.exports = {
  buildIssueListBlock,
  buildMilestoneBlock,
  buildRecommendationComment,
};
