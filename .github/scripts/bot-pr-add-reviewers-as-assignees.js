// SPDX-License-Identifier: Apache-2.0

/**
 * @fileoverview
 * Keeps individual requested reviewers mirrored as PR assignees.
 *
 * This is part of the generic "on-review" infrastructure.
 * Team reviewers are intentionally ignored (only individual users are assigned).
 * Requested reviewers are added as assignees, and reviewers are removed from
 * assignees after submitting a review.
 */

const { createLogger, BOT_NAME_ASSIGNEES } = require('./shared/helpers/reviewers-assignee-index.js');

const logger = createLogger(BOT_NAME_ASSIGNEES);

/**
 * Resolves the PR number from context.
 *
 * @param {Object} context - GitHub Actions context object
 * @returns {number|null} Valid PR number or null if invalid/missing
 */
function resolvePrNumber(context) {
  let prNumber;

  if (context.eventName === 'workflow_dispatch') {
    prNumber = Number(context.payload.inputs?.pr_number);
    if (!Number.isInteger(prNumber) || prNumber <= 0) {
      logger.warn('Invalid PR number supplied. Skipping.');
      return null;
    }
  } else {
    prNumber = context.payload.pull_request?.number;
    if (!Number.isInteger(prNumber) || prNumber <= 0) {
      logger.warn('No PR number found. Skipping.');
      return null;
    }
  }

  return prNumber;
}

/**
 * Extracts unique users to assign from requested reviewers.
 *
 * @param {Array<Object>} requestedReviewers - List of requested reviewers from PR
 * @param {Set<string>} currentAssignees - Set of current assignee logins
 * @returns {Set<string>} Set of logins that should be assigned
 */
function getUsersToAssign(requestedReviewers, currentAssignees) {
  const usersToAssign = new Set();

  for (const reviewer of requestedReviewers) {
    if (reviewer?.login && !currentAssignees.has(reviewer.login)) {
      usersToAssign.add(reviewer.login);
    }
  }
  return usersToAssign;
}

/**
 * Loads PR data from the event payload or GitHub API.
 *
 * @param {Object} params
 * @param {Object} params.github - GitHub Octokit client instance
 * @param {Object} params.context - GitHub Actions context object
 * @param {number} params.prNumber - Pull request number
 * @returns {Promise<Object>} Pull request payload
 */
async function loadPullRequest({ github, context, prNumber }) {
  const payloadPr = context.payload.pull_request;
  if (payloadPr && Number.isInteger(payloadPr.number)) {
    return payloadPr;
  }

  return (await github.rest.pulls.get({
    owner: context.repo.owner,
    repo: context.repo.repo,
    pull_number: prNumber
  })).data;
}

/**
 * Adds all requested individual reviewers as assignees.
 *
 * @param {Object} params
 * @param {Object} params.github - GitHub Octokit client instance
 * @param {Object} params.context - GitHub Actions context object
 * @param {number} params.prNumber - Pull request number
 * @param {Object} params.pr - Pull request payload
 * @returns {Promise<void>}
 */
async function addRequestedReviewersAsAssignees({ github, context, prNumber, pr }) {
  const owner = context.repo.owner;
  const repo = context.repo.repo;
  const requestedReviewers = pr.requested_reviewers || [];
  const requestedTeams = pr.requested_teams || [];

  const currentAssignees = new Set(
    (pr.assignees || []).map(a => a.login)
  );

  if (requestedTeams.length > 0) {
    logger.info(`${requestedTeams.length} team reviewer(s) detected but ignored (only individual users are assigned)`);
  }

  const assigneesList = Array.from(getUsersToAssign(requestedReviewers, currentAssignees));

  if (assigneesList.length === 0) {
    logger.log('No new users to assign. Done.');
    return;
  }

  logger.log(`Will assign: ${assigneesList.join(', ')}`);

  await github.rest.issues.addAssignees({
    owner,
    repo,
    issue_number: prNumber,
    assignees: assigneesList
  });

  logger.log(`✅ Successfully added ${assigneesList.length} reviewer(s) as assignee(s)`);
}

/**
 * Removes the reviewer from assignees after they submit a review.
 *
 * @param {Object} params
 * @param {Object} params.github - GitHub Octokit client instance
 * @param {Object} params.context - GitHub Actions context object
 * @param {number} params.prNumber - Pull request number
 * @param {Object} params.pr - Pull request payload
 * @returns {Promise<void>}
 */
async function removeReviewerFromAssignees({ github, context, prNumber, pr }) {
  const reviewerLogin = context.payload.review?.user?.login;
  if (!reviewerLogin) {
    logger.warn('No reviewer login found. Skipping.');
    return;
  }

  const currentAssignees = new Set(
    (pr.assignees || []).map(a => a.login)
  );

  if (!currentAssignees.has(reviewerLogin)) {
    logger.log(`${reviewerLogin} is not an assignee. Done.`);
    return;
  }

  await github.rest.issues.removeAssignees({
    owner: context.repo.owner,
    repo: context.repo.repo,
    issue_number: prNumber,
    assignees: [reviewerLogin]
  });

  logger.log(`✅ Removed ${reviewerLogin} from assignees after review submission`);
}

/**
 * Main handler that syncs requested reviewers and PR assignees.
 *
 * Triggered by:
 *   - `pull_request_target: review_requested`
 *   - `pull_request_review: submitted`
 *   - `workflow_dispatch` (for manual add-flow testing)
 *
 * @param {Object} params
 * @param {Object} params.github - GitHub Octokit client instance
 * @param {Object} params.context - GitHub Actions context object
 * @returns {Promise<void>}
 */
module.exports = async ({ github, context }) => {
  try {
    const prNumber = resolvePrNumber(context);
    if (!prNumber) return;

    logger.log(`Processing PR #${prNumber}`);

    const pr = await loadPullRequest({ github, context, prNumber });

    if (context.eventName === 'pull_request_review' && context.payload.action === 'submitted') {
      await removeReviewerFromAssignees({ github, context, prNumber, pr });
      return;
    }

    if (
      context.eventName === 'workflow_dispatch' ||
      (context.eventName === 'pull_request_target' && context.payload.action === 'review_requested')
    ) {
      await addRequestedReviewersAsAssignees({ github, context, prNumber, pr });
      return;
    }

    logger.info(`Unsupported event ${context.eventName}:${context.payload.action || 'unknown'}. Skipping.`);

  } catch (error) {
    logger.error('Failed:', error.message);
    if (error.status === 403) {
      logger.warn(`403 returned: ${error.message}`);
      return;
    }
    throw error;
  }
};
