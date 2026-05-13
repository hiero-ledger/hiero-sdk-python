// SPDX-License-Identifier: Apache-2.0
//
// tests/test-permissions.js
//
// Unit tests for helpers/permissions.js (getPermissionLevel, countApprovals).
// Run with: node .github/scripts/review-sync/tests/test-permissions.js

const { runTestSuite, createMockGithub } = require('./test-utils');
const { getPermissionLevel, countApprovals, clearPermissionCache } = require('../helpers/permissions');

// =============================================================================
// UNIT TESTS
// =============================================================================

const unitTests = [
  // ---------------------------------------------------------------------------
  // getPermissionLevel
  // ---------------------------------------------------------------------------
  {
    name: 'getPermissionLevel: uses role_name over permission (maintain case)',
    test: async () => {
      const mock = createMockGithub({
        roles: { sophie: { role_name: 'maintain', permission: 'write' } },
      });
      const result = await getPermissionLevel(mock, 'owner', 'repo', 'sophie');
      return result === 'maintain'; // NOT 'write'
    },
  },
  {
    name: 'getPermissionLevel: uses role_name over permission (admin case)',
    test: async () => {
      const mock = createMockGithub({
        roles: { admin: { role_name: 'admin', permission: 'admin' } },
      });
      const result = await getPermissionLevel(mock, 'owner', 'repo', 'admin');
      return result === 'admin';
    },
  },
  {
    name: 'getPermissionLevel: falls back to permission if role_name missing',
    test: async () => {
      const mock = createMockGithub({
        roles: { bob: { permission: 'write' } },
      });
      const result = await getPermissionLevel(mock, 'owner', 'repo', 'bob');
      return result === 'write';
    },
  },
  {
    name: 'getPermissionLevel: external contributor (404) returns none',
    test: async () => {
      const mock = createMockGithub({ roles: {} });
      const result = await getPermissionLevel(mock, 'owner', 'repo', 'unknown-user');
      return result === 'none';
    },
  },
  {
    name: 'getPermissionLevel: triage role returned correctly',
    test: async () => {
      const mock = createMockGithub({
        roles: { triager: { role_name: 'triage', permission: 'read' } },
      });
      const result = await getPermissionLevel(mock, 'owner', 'repo', 'triager');
      return result === 'triage';
    },
  },
  {
    name: 'getPermissionLevel: read role returned correctly',
    test: async () => {
      const mock = createMockGithub({
        roles: { reader: { role_name: 'read', permission: 'read' } },
      });
      const result = await getPermissionLevel(mock, 'owner', 'repo', 'reader');
      return result === 'read';
    },
  },

  // ---------------------------------------------------------------------------
  // countApprovals
  // ---------------------------------------------------------------------------
  {
    name: 'countApprovals: maintain counted as maintainerApprovals and coreApprovals, write as coreApprovals',
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
      const result = await countApprovals(mock, 'owner', 'repo', 1);
      return (
        result.maintainerApprovals === 1 &&
        result.coreApprovals === 2 &&
        result.softApprovals === 0 &&
        result.anyApproval === 2
      );
    },
  },
  {
    name: 'countApprovals: admin counted as maintainerApprovals and coreApprovals',
    test: async () => {
      const mock = createMockGithub({
        roles: {
          admin: { role_name: 'admin', permission: 'admin' },
        },
        reviews: [
          { user: { login: 'admin' }, state: 'APPROVED', submitted_at: '2026-01-01T00:00:00Z' },
        ],
      });
      const result = await countApprovals(mock, 'owner', 'repo', 1);
      return result.maintainerApprovals === 1 && result.coreApprovals === 1 && result.anyApproval === 1;
    },
  },
  {
    name: 'countApprovals: external contributor counted as softApprovals',
    test: async () => {
      const mock = createMockGithub({
        roles: {},
        reviews: [
          { user: { login: 'external' }, state: 'APPROVED', submitted_at: '2026-01-01T00:00:00Z' },
        ],
      });
      const result = await countApprovals(mock, 'owner', 'repo', 1);
      return (
        result.maintainerApprovals === 0 &&
        result.coreApprovals === 0 &&
        result.softApprovals === 1 &&
        result.anyApproval === 1
      );
    },
  },
  {
    name: 'countApprovals: CHANGES_REQUESTED not counted in any counter',
    test: async () => {
      const mock = createMockGithub({
        roles: {
          bob: { role_name: 'write', permission: 'write' },
        },
        reviews: [
          { user: { login: 'bob' }, state: 'CHANGES_REQUESTED', submitted_at: '2026-01-01T00:00:00Z' },
        ],
      });
      const result = await countApprovals(mock, 'owner', 'repo', 1);
      return result.anyApproval === 0;
    },
  },
  {
    name: 'countApprovals: no reviews returns all zeros',
    test: async () => {
      const mock = createMockGithub({ roles: {}, reviews: [] });
      const result = await countApprovals(mock, 'owner', 'repo', 1);
      return (
        result.maintainerApprovals === 0 &&
        result.coreApprovals === 0 &&
        result.softApprovals === 0 &&
        result.anyApproval === 0
      );
    },
  },
  {
    name: 'countApprovals: mixed roles — 1 admin + 1 write + 1 external',
    test: async () => {
      const mock = createMockGithub({
        roles: {
          admin: { role_name: 'admin', permission: 'admin' },
          committer: { role_name: 'write', permission: 'write' },
        },
        reviews: [
          { user: { login: 'admin' }, state: 'APPROVED', submitted_at: '2026-01-01T00:00:00Z' },
          { user: { login: 'committer' }, state: 'APPROVED', submitted_at: '2026-01-02T00:00:00Z' },
          { user: { login: 'random' }, state: 'APPROVED', submitted_at: '2026-01-03T00:00:00Z' },
        ],
      });
      const result = await countApprovals(mock, 'owner', 'repo', 1);
      return (
        result.maintainerApprovals === 1 &&
        result.coreApprovals === 2 &&
        result.softApprovals === 1 &&
        result.anyApproval === 3
      );
    },
  },
  {
    name: 'countApprovals: DISMISSED approval is not counted',
    test: async () => {
      const mock = createMockGithub({
        roles: {
          sophie: { role_name: 'maintain', permission: 'write' },
        },
        reviews: [
          { user: { login: 'sophie' }, state: 'APPROVED', submitted_at: '2026-01-01T00:00:00Z' },
          { user: { login: 'sophie' }, state: 'DISMISSED', submitted_at: '2026-01-02T00:00:00Z' },
        ],
      });
      const result = await countApprovals(mock, 'owner', 'repo', 1);
      return result.maintainerApprovals === 0 && result.anyApproval === 0;
    },
  },
];

// =============================================================================
// TEST RUNNER
// =============================================================================

async function runUnitTests() {
  console.log('🔬 UNIT TESTS (permissions)');
  console.log('='.repeat(70));
  let passed = 0;
  let failed = 0;
  for (const test of unitTests) {
    clearPermissionCache();
    try {
      const result = await Promise.resolve(test.test());
      if (result) {
        console.log(`✅ ${test.name}`);
        passed++;
      } else {
        console.log(`❌ ${test.name}`);
        failed++;
      }
    } catch (error) {
      console.log(`❌ ${test.name} - Error: ${error.message}`);
      failed++;
    }
  }
  console.log('\n' + '-'.repeat(70));
  console.log(`Unit Tests: ${passed} passed, ${failed} failed`);
  return { total: unitTests.length, passed, failed };
}

runTestSuite('PERMISSIONS TEST SUITE', [], async () => true, [
  { label: 'Unit Tests', run: runUnitTests },
]);
