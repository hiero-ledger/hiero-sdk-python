// SPDX-License-Identifier: Apache-2.0

/**
 * @fileoverview
 * Automatically adds requested individual reviewers as assignees on Pull Requests.
 *
 * This is part of the generic "on-review" infrastructure.
 * Team reviewers are intentionally ignored (only individual users are assigned).
 * Caps the number of assignees at MAX_ASSIGNEES (default: 2).
 */

const { createLogger, MAX_ASSIGNEES, BOT_NAME_ASSIGNEES } = require('./shared/helpers/reviewers-assignee-index.js');

const logger = createLogger(BOT_NAME_ASSIGNEES);

/**
 * Resolves the PR number from context (pull_request_target or workflow_dispatch).
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
    // pull_request_target
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
 * Logs a warning if some reviewers were dropped due to the assignee cap.
 *
 * @param {Set<string>} usersToAssign
 */
function logAssigneeCapWarning(usersToAssign, maxToAdd) {
  if (usersToAssign.size > maxToAdd) {
    const dropped = Array.from(usersToAssign).slice(maxToAdd);
    logger.warn(`Assignee cap (${MAX_ASSIGNEES}) reached. Dropping: ${dropped.join(', ')}`);
  }
}

/**
 * Main handler that adds requested reviewers as assignees on a PR.
 *
 * Triggered by:
 *   - `pull_request_target: review_requested`
 *   - `workflow_dispatch` (for manual testing)
 *
 * Behavior:
 *   - Only processes individual reviewers (`requested_reviewers`)
 *   - Ignores team reviewers (`requested_teams`)
 *   - Skips users who are already assignees
 *   - Caps at `MAX_ASSIGNEES` (default: 2)
 *   - Logs a warning when reviewers are dropped due to the cap
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

    const owner = context.repo.owner;
    const repo = context.repo.repo;

    logger.log(`Processing PR #${prNumber}`);

    const payloadPr = context.payload.pull_request;
    const pr = (payloadPr && Number.isInteger(payloadPr.number))
      ? payloadPr
      : (await github.rest.pulls.get({
          owner,
          repo,
          pull_number: prNumber
        })).data;

    const requestedReviewers = pr.requested_reviewers || [];
    const requestedTeams = pr.requested_teams || [];

    const currentAssignees = new Set(
      (pr.assignees || []).map(a => a.login)
    );

    if (requestedTeams.length > 0) {
      logger.info(`${requestedTeams.length} team reviewer(s) detected but ignored (only individual users are assigned)`);
    }
    const usersToAssign = getUsersToAssign(requestedReviewers, currentAssignees);
    const currentCount = currentAssignees.size;
    const maxNewAssignees = Math.max(0, MAX_ASSIGNEES - currentCount);
    const assigneesList = Array.from(usersToAssign).slice(0, maxNewAssignees);

    if (assigneesList.length === 0) {
      logger.log('No new users to assign. Done.');
      return;
    }

    logger.log(`Will assign: ${assigneesList.join(', ')}`);
    logAssigneeCapWarning(usersToAssign, maxNewAssignees);

    await github.rest.issues.addAssignees({
      owner,
      repo,
      issue_number: prNumber,
      assignees: assigneesList
    });

    logger.log(`✅ Successfully added ${assigneesList.length} reviewer(s) as assignee(s)`);

  } catch (error) {
    logger.error('Failed:', error.message);
    if (error.status === 403) {
      logger.warn(`403 returned: ${error.message}`);
      return;
    }
    throw error;
  }
};
