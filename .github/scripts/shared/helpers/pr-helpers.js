// ---------------------------------------------------------------------------
// PR parsing and comment helpers
// ---------------------------------------------------------------------------

const { CONFIG } = require('../config');

/**
 * Extracts the first linked issue number from a PR body using closing keywords.
 * Supports: fixes, closes, resolves, fix, close, resolve (with or without colon),
 * and cross-repo references (owner/repo#123) as well as plain #123.
 * Input is capped at 50 000 chars to guard against pathologically large PR bodies.
 *
 * @param {string} prBody - Raw PR description text.
 * @returns {number|null} Linked issue number, or null if none found.
 */
function extractLinkedIssueNumber(prBody) {
  const safe  = prBody.length > 50000 ? prBody.substring(0, 50000) : prBody;
  const regex = /(fixes|closes|resolves|fix|close|resolve):?\s*(?:[\w-]+\/[\w-]+)?#(\d+)/gi;
  const match = regex.exec(safe);
  return match ? parseInt(match[2], 10) : null;
}

/**
 * Returns true if the bot has already posted a recommendation comment on this PR.
 * Matches by the HTML marker string embedded at the top of every comment we post.
 * Returns false on API failure to avoid blocking the run.
 *
 * @param {import('@actions/github').GitHub} github
 * @param {string} owner    - Repo owner.
 * @param {string} repo     - Repo name.
 * @param {number} prNumber - PR number.
 * @returns {Promise<boolean>}
 */
async function alreadyCommented(github, owner, repo, prNumber) {
  try {
    const { data } = await github.rest.issues.listComments({
      owner, repo, issue_number: prNumber, per_page: 100,
    });
    return data.some(c => c.body?.includes(CONFIG.commentMarker));
  } catch {
    return false;
  }
}

/**
 * Posts a comment on a PR and logs the outcome.
 *
 * @param {import('@actions/github').GitHub} github
 * @param {string} owner    - Repo owner.
 * @param {string} repo     - Repo name.
 * @param {number} prNumber - PR number.
 * @param {string} body     - Comment body.
 * @param {object} core     - @actions/core logger.
 * @returns {Promise<boolean>} True if posted successfully, false otherwise.
 */
async function postComment(github, owner, repo, prNumber, body, core) {
  try {
    await github.rest.issues.createComment({ owner, repo, issue_number: prNumber, body });
    core.info(`Posted recommendation comment to PR #${prNumber}`);
    return true;
  } catch (error) {
    core.error(`Failed to post comment: ${error.message}`);
    return false;
  }
}

module.exports = {
  extractLinkedIssueNumber,
  alreadyCommented,
  postComment,
};
