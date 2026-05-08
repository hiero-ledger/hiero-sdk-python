// SPDX-License-Identifier: Apache-2.0
//
// helpers/status.js
//
// Read-only review status reporting built on top of the review queue model.
// This helper does not create labels, change assignments, comment on PRs, or
// mutate review state. It only converts existing labels and review data into a
// concise status message that can be printed in workflow logs or summaries.

const { ALL_QUEUE_LABEL_NAMES, QUEUE_LABELS } = require('./constants');
const { determineLabel } = require('./labels');

function normalizeLabels(labels = []) {
  return labels
    .map((label) => (typeof label === 'string' ? label : label?.name))
    .filter(Boolean);
}

function hasChangesRequested(latestReviewStates = new Map()) {
  if (!(latestReviewStates instanceof Map)) return false;
  return [...latestReviewStates.values()].some((state) => state === 'CHANGES_REQUESTED');
}

function describeQueueLabel(labelName) {
  switch (labelName) {
    case QUEUE_LABELS.JUNIOR.name:
      return {
        waitingOn: 'junior committer review',
        nextAction: 'Initial review is needed.',
      };
    case QUEUE_LABELS.COMMITTERS.name:
      return {
        waitingOn: 'committer review',
        nextAction: 'A committer approval is needed.',
      };
    case QUEUE_LABELS.MAINTAINERS.name:
      return {
        waitingOn: 'maintainer review',
        nextAction: 'A maintainer approval is needed.',
      };
    case QUEUE_LABELS.MERGE.name:
      return {
        waitingOn: 'merge',
        nextAction: 'Required review approvals are satisfied.',
      };
    default:
      return {
        waitingOn: 'review',
        nextAction: 'Review status should be checked.',
      };
  }
}

function normalizeApprovals(approvals = {}) {
  const maintainerApprovals = approvals.maintainerApprovals || 0;
  const coreApprovals = approvals.coreApprovals || 0;
  const softApprovals = approvals.softApprovals || 0;

  return {
    maintainerApprovals,
    coreApprovals,
    softApprovals,
    anyApproval: approvals.anyApproval || coreApprovals + softApprovals,
  };
}

/**
 * Build a read-only status report for a pull request.
 *
 * @param {object} params
 * @param {number} params.prNumber
 * @param {Array<string|{name:string}>} params.labels
 * @param {{ maintainerApprovals?: number, coreApprovals?: number, softApprovals?: number, anyApproval?: number }} params.approvals
 * @param {Map<string, string>} params.latestReviewStates
 * @returns {object} Structured review status report.
 */
function buildReviewStatus({ prNumber, labels = [], approvals, latestReviewStates = new Map() }) {
  const labelNames = normalizeLabels(labels);
  const currentQueueLabels = labelNames.filter((name) => ALL_QUEUE_LABEL_NAMES.includes(name));
  const normalizedApprovals = normalizeApprovals(approvals);
  const expectedQueueLabel = determineLabel(normalizedApprovals);
  const changesRequested = hasChangesRequested(latestReviewStates);

  let currentState = expectedQueueLabel.name;
  let waitingOn;
  let nextAction;

  if (changesRequested) {
    currentState = 'changes requested';
    waitingOn = 'author updates';
    nextAction = 'The author should address the requested changes.';
  } else {
    ({ waitingOn, nextAction } = describeQueueLabel(expectedQueueLabel.name));
  }

  return {
    prNumber,
    currentState,
    expectedQueueLabel: expectedQueueLabel.name,
    currentQueueLabels,
    staleQueueLabels: currentQueueLabels.filter((name) => name !== expectedQueueLabel.name),
    approvals: normalizedApprovals,
    changesRequested,
    waitingOn,
    nextAction,
    summary: `PR #${prNumber} is waiting on ${waitingOn}.`,
  };
}

function formatStatusForLog(status) {
  const currentLabels = status.currentQueueLabels.length > 0
    ? status.currentQueueLabels.join(', ')
    : 'none';
  const staleLabels = status.staleQueueLabels.length > 0
    ? status.staleQueueLabels.join(', ')
    : 'none';

  return [
    `Review status: ${status.expectedQueueLabel}`,
    `Current state: ${status.currentState}`,
    `Waiting on: ${status.waitingOn}`,
    `Next action: ${status.nextAction}`,
    `Current queue labels: ${currentLabels}`,
    `Stale queue labels: ${staleLabels}`,
    `Approvals: maintainer=${status.approvals.maintainerApprovals}, core=${status.approvals.coreApprovals}, soft=${status.approvals.softApprovals}`,
  ].join('\n');
}

module.exports = {
  buildReviewStatus,
  formatStatusForLog,
  normalizeLabels,
};
