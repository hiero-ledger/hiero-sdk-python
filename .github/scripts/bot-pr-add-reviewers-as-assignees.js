// SPDX-License-Identifier: Apache-2.0

/**
 * @fileoverview
 * Manages requested individual reviewers as PR assignees.
 *
 * - On `review_requested` (pull_request_target): adds the reviewer as an assignee (no cap).
 * - On `workflow_run` (triggered by Bot - Capture PR Review): removes the reviewer from
 *   assignees using a write-token that works for fork PRs. The reviewer login and PR number
 *   are read from the artifact written by the capture workflow.
 * - Team reviewers are intentionally ignored (only individual users are assigned).
 */

const { createLogger, BOT_NAME_ASSIGNEES } = require('./shared/helpers/reviewers-assignee-index.js');

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
 * Adds requested reviewers as PR assignees (no cap on count).
 *
 * @param {Object} params
 * @param {Object} params.github - GitHub Octokit client instance
 * @param {Object} params.context - GitHub Actions context object
 */
async function addReviewersAsAssignees({ github, context }) {
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
    const assigneesList = Array.from(usersToAssign);

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

  } catch (error) {
    logger.error('Failed:', error.message);
    if (error.status === 403) {
      logger.warn(`403 returned: ${error.message}`);
      return;
    }
    throw error;
  }
}

/**
 * Removes a reviewer from PR assignees after they submit their review.
 * Called from the workflow_run removal job via named export, passing reviewer
 * login and PR number read from the capture workflow's artifact.
 *
 * Explicit params take priority; falls back to context.payload for direct calls.
 *
 * @param {Object} params
 * @param {Object} params.github - GitHub Octokit client instance
 * @param {Object} params.context - GitHub Actions context object
 * @param {string} [params.reviewer] - Reviewer login (overrides context payload)
 * @param {number} [params.prNumber] - PR number (overrides context payload)
 */
async function removeReviewerFromAssignees({ github, context, reviewer: explicitReviewer, prNumber: explicitPrNumber }) {
  try {
    const reviewer = explicitReviewer ?? context.payload?.review?.user?.login;
    const prNumber = explicitPrNumber ?? context.payload?.pull_request?.number;

    if (!reviewer || !Number.isInteger(prNumber) || prNumber <= 0) {
      logger.warn('Missing reviewer login or PR number. Skipping removal.');
      return;
    }

    const owner = context.repo.owner;
    const repo = context.repo.repo;

    // Fetch live PR data to avoid acting on a stale event payload snapshot.
    const livePr = (await github.rest.pulls.get({ owner, repo, pull_number: prNumber })).data;
    const currentAssignees = (livePr.assignees || []).map(a => a.login);

    if (!currentAssignees.includes(reviewer)) {
      logger.log(`${reviewer} is not an assignee on PR #${prNumber}. Nothing to remove.`);
      return;
    }

    logger.log(`Removing ${reviewer} from assignees on PR #${prNumber}`);

    await github.rest.issues.removeAssignees({
      owner,
      repo,
      issue_number: prNumber,
      assignees: [reviewer]
    });

    logger.log(`✅ Successfully removed ${reviewer} from assignee(s)`);

  } catch (error) {
    logger.error('Failed to remove assignee:', error.message);
    if (error.status === 403) {
      logger.warn(`403 returned: ${error.message}`);
      return;
    }
    throw error;
  }
}

/**
 * Entry point for the add flow (pull_request_target + workflow_dispatch).
 * The remove flow is invoked directly via the named export from the workflow_run job.
 *
 * @param {Object} params
 * @param {Object} params.github - GitHub Octokit client instance
 * @param {Object} params.context - GitHub Actions context object
 * @returns {Promise<void>}
 */
module.exports = async ({ github, context }) => {
  const { eventName } = context;
  const action = context.payload.action;

  if (
    (eventName === 'pull_request_target' && action === 'review_requested') ||
    eventName === 'workflow_dispatch'
  ) {
    await addReviewersAsAssignees({ github, context });
  } else {
    logger.warn(`Unhandled event: ${eventName} / ${action}. Skipping.`);
  }
};

module.exports.removeReviewerFromAssignees = removeReviewerFromAssignees;
