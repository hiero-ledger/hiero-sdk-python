// .github/scripts/bot-issue-assign-on-comment.js
//
// Replaces bot-beginner-assign-on-comment.js and bot-gfi_assign_on_comment.js.
//
// Triggered by the `issue_comment` (created) event. Figures out which
// difficulty level (if any) applies to the commented-on issue, then hands
// off to the shared engine with that level's config. All label-specific
// behavior lives in .github/scripts/configs/assignment-levels.js; this file
// is just wiring.
//
// Supporting a new difficulty level (e.g. "advanced") requires zero changes
// here — just add/enable its config in assignment-levels.js.

const { runAssignmentFlow, issueHasLabel } = require('./shared/issue-assign-core.js');
const { LEVEL_CONFIGS } = require('./configs/assignment-levels.js');

module.exports = async ({ github, context }) => {
  try {
    const issue = context.payload.issue;

    if (!issue) {
      console.log('[assign-bot] No issue in payload. Exiting.');
      return;
    }

    const levelConfig = LEVEL_CONFIGS.find((config) => issueHasLabel(issue, config.label));

    if (!levelConfig) {
      console.log(`[assign-bot] Issue #${issue.number} has no recognized difficulty label. Exiting.`);
      return;
    }

    console.log(`[assign-bot] Issue #${issue.number} matched level "${levelConfig.label}".`);
    await runAssignmentFlow({ github, context, levelConfig });
  } catch (error) {
    console.error('[assign-bot] Unexpected error:', {
      message: error.message,
      status: error.status,
      issue: context.payload?.issue?.number,
      comment: context.payload?.comment?.id,
    });
  }
};
