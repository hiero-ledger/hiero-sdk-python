// .github/scripts/bot-issue-assign-on-comment.js
//
// Assigns user to a issue by commenting /assign

const { runAssignmentFlow } = require('./shared');

module.exports = async ({ github, context }) => {
  try {
    await runAssignmentFlow({ github, context });
  } catch (error) {
    console.error('[assign-bot] Unexpected error:', {
      message: error.message,
      status: error.status,
      issue: context.payload?.issue?.number,
      comment: context.payload?.comment?.id,
    });
  }
};
