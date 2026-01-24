/*
------------------------------------------------------------------------------
Working On It Bot

Executes When:
  - Triggered by GitHub Actions on 'issue_comment' (created)

Goal:
  Allows an assignee or PR author to signal they are active by commenting "/working".
  This acts as a signal to other inactivity bots to skip their next cleanup cycle.

Safeguards:
  - Works on both Issues and PRs
  - Only the Assignee (for issues) or Author (for PRs) can trigger it
  - Reacts with an emoji to confirm receipt
------------------------------------------------------------------------------
*/

function isValidContext(comment) {
  if (!comment?.body || !comment?.user?.login) return false;
  if (comment.user.type === "Bot") return false;
  return true;
}

function commentRequestsWorking(body) {
  return typeof body === "string" && /(^|\s)\/working(\s|$)/i.test(body);
}

function isAuthorizedUser(issue, username) {
  // If it's a PR, the author can trigger it
  if (issue.pull_request && issue.user.login === username) {
    return true;
  }
  // If it's an issue (or PR), any assignee can trigger it
  return issue.assignees?.some((a) => a.login === username);
}

module.exports = async ({ github, context }) => {
  try {
    const { issue, comment } = context.payload;
    const { owner, repo } = context.repo;

    // 1. Basic Validation
    if (!isValidContext(comment)) return;

    // 2. Check for Command
    if (!commentRequestsWorking(comment.body)) return;

    const username = comment.user.login;
    console.log(
      `[working] Command detected by ${username} on #${issue.number}`,
    );

    // 3. Authorization Check
    if (!isAuthorizedUser(issue, username)) {
      console.log(
        `[working] User ${username} is not assigned or the author. Ignoring.`,
      );
      return;
    }

    // 4. Acknowledge with a reaction
    // We don't need to save state here; the other bots will query the comment timestamp directly.
    await github.rest.reactions.createForIssueComment({
      owner,
      repo,
      comment_id: comment.id,
      content: "eyes",
    });

    console.log(
      `[working] Acknowledged command from ${username} with reaction.`,
    );
  } catch (error) {
    console.error("[working] Error:", error.message);
    // Don't throw, just log, so we don't fail the workflow pipeline for minor API hiccups
  }
};
