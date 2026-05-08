// SPDX-License-Identifier: Apache-2.0
//
// tests/test-status.js
//
// Unit tests for helpers/status.js.
// Run with: node .github/scripts/review-sync/tests/test-status.js

const { runTestSuite } = require('./test-utils');
const { buildReviewStatus, formatStatusForLog, normalizeLabels } = require('../helpers/status');

const emptyReviews = new Map();

const unitTests = [
  {
    name: 'normalizeLabels accepts GitHub label objects and strings',
    test: () => {
      const labels = normalizeLabels([{ name: 'queue:committers' }, 'skill: beginner', {}, null]);
      return labels.length === 2 && labels.includes('queue:committers') && labels.includes('skill: beginner');
    },
  },
  {
    name: 'no approvals reports junior committer review',
    test: () => {
      const status = buildReviewStatus({
        prNumber: 10,
        labels: [],
        approvals: { maintainerApprovals: 0, coreApprovals: 0, softApprovals: 0, anyApproval: 0 },
        latestReviewStates: emptyReviews,
      });

      return status.expectedQueueLabel === 'queue:junior-committer' &&
        status.waitingOn === 'junior committer review' &&
        status.currentQueueLabels.length === 0;
    },
  },
  {
    name: 'soft approval reports committer review',
    test: () => {
      const status = buildReviewStatus({
        prNumber: 11,
        labels: [{ name: 'queue:junior-committer' }],
        approvals: { maintainerApprovals: 0, coreApprovals: 0, softApprovals: 1, anyApproval: 1 },
        latestReviewStates: emptyReviews,
      });

      return status.expectedQueueLabel === 'queue:committers' &&
        status.waitingOn === 'committer review' &&
        status.staleQueueLabels.includes('queue:junior-committer');
    },
  },
  {
    name: 'core approval reports maintainer review',
    test: () => {
      const status = buildReviewStatus({
        prNumber: 12,
        labels: [{ name: 'queue:committers' }],
        approvals: { maintainerApprovals: 0, coreApprovals: 1, softApprovals: 0, anyApproval: 1 },
        latestReviewStates: emptyReviews,
      });

      return status.expectedQueueLabel === 'queue:maintainers' &&
        status.waitingOn === 'maintainer review';
    },
  },
  {
    name: 'maintainer and core approvals report ready to merge',
    test: () => {
      const status = buildReviewStatus({
        prNumber: 13,
        labels: [{ name: 'queue:maintainers' }],
        approvals: { maintainerApprovals: 1, coreApprovals: 2, softApprovals: 0, anyApproval: 2 },
        latestReviewStates: emptyReviews,
      });

      return status.expectedQueueLabel === 'status: ready-to-merge' &&
        status.waitingOn === 'merge';
    },
  },
  {
    name: 'changes requested reports author updates before queue state',
    test: () => {
      const status = buildReviewStatus({
        prNumber: 14,
        labels: [{ name: 'queue:committers' }],
        approvals: { maintainerApprovals: 0, coreApprovals: 0, softApprovals: 1, anyApproval: 1 },
        latestReviewStates: new Map([['alice', 'CHANGES_REQUESTED']]),
      });

      return status.currentState === 'changes requested' &&
        status.waitingOn === 'author updates' &&
        status.nextAction.includes('address');
    },
  },
  {
    name: 'missing latest review states defaults to no changes requested',
    test: () => {
      const status = buildReviewStatus({
        prNumber: 15,
        labels: [],
        approvals: { maintainerApprovals: 0, coreApprovals: 0, softApprovals: 0, anyApproval: 0 },
      });

      return status.changesRequested === false &&
        status.waitingOn === 'junior committer review';
    },
  },
  {
    name: 'formatStatusForLog includes key report fields',
    test: () => {
      const status = buildReviewStatus({
        prNumber: 16,
        labels: [{ name: 'queue:junior-committer' }],
        approvals: { maintainerApprovals: 0, coreApprovals: 0, softApprovals: 0, anyApproval: 0 },
        latestReviewStates: emptyReviews,
      });
      const output = formatStatusForLog(status);

      return output.includes('Review status: queue:junior-committer') &&
        output.includes('Waiting on: junior committer review') &&
        output.includes('Approvals: maintainer=0, core=0, soft=0');
    },
  },
];

async function runUnitTests() {
  console.log('UNIT TESTS (status)');
  console.log('='.repeat(70));
  let passed = 0;
  let failed = 0;
  for (const t of unitTests) {
    try {
      const result = await Promise.resolve(t.test());
      if (result) { console.log(`PASS ${t.name}`); passed++; }
      else { console.log(`FAIL ${t.name}`); failed++; }
    } catch (error) { console.log(`FAIL ${t.name} - Error: ${error.message}`); failed++; }
  }
  console.log('\n' + '-'.repeat(70));
  console.log(`Unit Tests: ${passed} passed, ${failed} failed`);
  return { total: unitTests.length, passed, failed };
}

runTestSuite('STATUS TEST SUITE', [], async () => true, [
  { label: 'Unit Tests', run: runUnitTests },
]);
