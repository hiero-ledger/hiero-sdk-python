// SPDX-License-Identifier: Apache-2.0
//
// tests/test-labels.js
//
// Unit tests for helpers/labels.js (determineLabel, ensureLabel, syncLabel).
// Run with: node .github/scripts/review-sync/tests/test-labels.js

const { runTestSuite, createMockGithub } = require('./test-utils');
const { determineLabel, ensureLabel, syncLabel } = require('../helpers/labels');
const { QUEUE_LABELS } = require('../helpers/constants');

const unitTests = [
  {
    name: 'determineLabel: 0 approvals → queue:junior-committer',
    test: () => {
      const r = determineLabel({ maintainerApproval: 0, writeApproval: 0, softApproval: 0, anyApproval: 0 });
      return r.name === 'queue:junior-committer';
    },
  },
  {
    name: 'determineLabel: 1 soft approval → queue:committers',
    test: () => {
      const r = determineLabel({ maintainerApproval: 0, writeApproval: 0, softApproval: 1, anyApproval: 1 });
      return r.name === 'queue:committers';
    },
  },
  {
    name: 'determineLabel: 1 write approval → queue:maintainers',
    test: () => {
      const r = determineLabel({ maintainerApproval: 0, writeApproval: 1, softApproval: 0, anyApproval: 1 });
      return r.name === 'queue:maintainers';
    },
  },
  {
    name: 'determineLabel: 2 write + 0 maintainer → queue:maintainers (NOT status: ready-to-merge)',
    test: () => {
      const r = determineLabel({ maintainerApproval: 0, writeApproval: 2, softApproval: 0, anyApproval: 2 });
      return r.name === 'queue:maintainers';
    },
  },
  {
    name: 'determineLabel: 1 maintainer alone → queue:maintainers (NOT status: ready-to-merge, needs 2 reviews)',
    test: () => {
      // Sophie's edge case: maintainer approves first, only 1 total review
      const r = determineLabel({ maintainerApproval: 1, writeApproval: 0, softApproval: 0, anyApproval: 1 });
      return r.name === 'queue:maintainers';
    },
  },
  {
    name: 'determineLabel: 1 maintainer + 1 write → status: ready-to-merge (2 reviews satisfied)',
    test: () => {
      const r = determineLabel({ maintainerApproval: 1, writeApproval: 1, softApproval: 0, anyApproval: 2 });
      return r.name === 'status: ready-to-merge';
    },
  },
  {
    name: 'determineLabel: 1 maintainer + 1 soft → queue:maintainers (soft approvals do not count as core review)',
    test: () => {
      const r = determineLabel({ maintainerApproval: 1, writeApproval: 0, softApproval: 1, anyApproval: 2 });
      return r.name === 'queue:maintainers';
    },
  },
  {
    name: 'determineLabel: 3 soft, 0 write → queue:committers',
    test: () => {
      const r = determineLabel({ maintainerApproval: 0, writeApproval: 0, softApproval: 3, anyApproval: 3 });
      return r.name === 'queue:committers';
    },
  },
  {
    name: 'ensureLabel: creates label when missing',
    test: async () => {
      const mock = createMockGithub({ existingLabels: {} });
      await ensureLabel(mock, 'o', 'r', QUEUE_LABELS.JUNIOR, false);
      return mock.calls.labelsCreated.length === 1 && mock.calls.labelsCreated[0].name === 'queue:junior-committer';
    },
  },
  {
    name: 'ensureLabel: skips when label exists',
    test: async () => {
      const mock = createMockGithub({ existingLabels: { 'queue:junior-committer': true } });
      await ensureLabel(mock, 'o', 'r', QUEUE_LABELS.JUNIOR, false);
      return mock.calls.labelsCreated.length === 0;
    },
  },
  {
    name: 'ensureLabel: dry run does not create',
    test: async () => {
      const mock = createMockGithub({ existingLabels: {} });
      await ensureLabel(mock, 'o', 'r', QUEUE_LABELS.JUNIOR, true);
      return mock.calls.labelsCreated.length === 0;
    },
  },
  {
    name: 'syncLabel: no approvals, no labels → adds junior-committer',
    test: async () => {
      const mock = createMockGithub({ roles: {}, reviews: [] });
      const changed = await syncLabel(mock, 'o', 'r', { number: 1, labels: [] }, false);
      return changed === true && mock.calls.labelsAdded[0] === 'queue:junior-committer';
    },
  },
  {
    name: 'syncLabel: already correct, no stale → returns false',
    test: async () => {
      const mock = createMockGithub({ roles: {}, reviews: [] });
      const changed = await syncLabel(mock, 'o', 'r', { number: 1, labels: [{ name: 'queue:junior-committer' }] }, false);
      return changed === false && mock.calls.labelsAdded.length === 0;
    },
  },
  {
    name: 'syncLabel: stale label → adds correct, removes stale',
    test: async () => {
      const mock = createMockGithub({
        roles: {
          sophie: { role_name: 'maintain', permission: 'write' },
          bob: { role_name: 'write', permission: 'write' },
        },
        reviews: [
          { user: { login: 'sophie' }, state: 'APPROVED', submitted_at: '2026-01-01T00:00:00Z' },
          { user: { login: 'bob' }, state: 'APPROVED', submitted_at: '2026-01-02T00:00:00Z' },
        ],
      });
      const changed = await syncLabel(mock, 'o', 'r', { number: 1, labels: [{ name: 'queue:junior-committer' }] }, false);
      return changed === true && mock.calls.labelsAdded.includes('status: ready-to-merge') && mock.calls.labelsRemoved.includes('queue:junior-committer');
    },
  },
  {
    name: 'syncLabel: dry run logs but does not modify',
    test: async () => {
      const mock = createMockGithub({ roles: {}, reviews: [] });
      const changed = await syncLabel(mock, 'o', 'r', { number: 1, labels: [{ name: 'queue:committers' }] }, true);
      return changed === true && mock.calls.labelsAdded.length === 0;
    },
  },
  {
    name: 'syncLabel: correct + stale present → cleans up stale',
    test: async () => {
      const mock = createMockGithub({ roles: {}, reviews: [] });
      const pr = { number: 1, labels: [{ name: 'queue:junior-committer' }, { name: 'queue:committers' }] };
      const changed = await syncLabel(mock, 'o', 'r', pr, false);
      return changed === true && mock.calls.labelsRemoved.includes('queue:committers');
    },
  },
];

async function runUnitTests() {
  console.log('🔬 UNIT TESTS (labels)');
  console.log('='.repeat(70));
  let passed = 0;
  let failed = 0;
  for (const t of unitTests) {
    try {
      const result = await Promise.resolve(t.test());
      if (result) { console.log(`✅ ${t.name}`); passed++; }
      else { console.log(`❌ ${t.name}`); failed++; }
    } catch (error) { console.log(`❌ ${t.name} - Error: ${error.message}`); failed++; }
  }
  console.log('\n' + '-'.repeat(70));
  console.log(`Unit Tests: ${passed} passed, ${failed} failed`);
  return { total: unitTests.length, passed, failed };
}

runTestSuite('LABELS TEST SUITE', [], async () => true, [
  { label: 'Unit Tests', run: runUnitTests },
]);
