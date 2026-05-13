// SPDX-License-Identifier: Apache-2.0
//
// tests/test-reviews.js
//
// Unit tests for helpers/reviews.js (getLatestReviewStates).
// Run with: node .github/scripts/review-sync/tests/test-reviews.js

const { runTestSuite, createMockGithub } = require('./test-utils');
const { getLatestReviewStates } = require('../helpers/reviews');

const unitTests = [
  {
    name: 'getLatestReviewStates: single APPROVED → returns approved',
    test: async () => {
      const mock = createMockGithub({
        reviews: [
          { user: { login: 'alice' }, state: 'APPROVED', submitted_at: '2026-01-01T00:00:00Z' },
        ],
      });
      const states = await getLatestReviewStates(mock, 'o', 'r', 1);
      return states.size === 1 && states.get('alice') === 'APPROVED';
    },
  },
  {
    name: 'getLatestReviewStates: DISMISSED deletes prior APPROVED',
    test: async () => {
      const mock = createMockGithub({
        reviews: [
          { user: { login: 'alice' }, state: 'APPROVED', submitted_at: '2026-01-01T00:00:00Z' },
          { user: { login: 'alice' }, state: 'DISMISSED', submitted_at: '2026-01-02T00:00:00Z' },
        ],
      });
      const states = await getLatestReviewStates(mock, 'o', 'r', 1);
      return states.size === 0;
    },
  },
  {
    name: 'getLatestReviewStates: COMMENTED is ignored',
    test: async () => {
      const mock = createMockGithub({
        reviews: [
          { user: { login: 'bob' }, state: 'COMMENTED', submitted_at: '2026-01-01T00:00:00Z' },
        ],
      });
      const states = await getLatestReviewStates(mock, 'o', 'r', 1);
      return states.size === 0;
    },
  },
  {
    name: 'getLatestReviewStates: later APPROVED overwrites CHANGES_REQUESTED',
    test: async () => {
      const mock = createMockGithub({
        reviews: [
          { user: { login: 'alice' }, state: 'CHANGES_REQUESTED', submitted_at: '2026-01-01T00:00:00Z' },
          { user: { login: 'alice' }, state: 'APPROVED', submitted_at: '2026-01-02T00:00:00Z' },
        ],
      });
      const states = await getLatestReviewStates(mock, 'o', 'r', 1);
      return states.get('alice') === 'APPROVED';
    },
  },
  {
    name: 'getLatestReviewStates: later CHANGES_REQUESTED overwrites APPROVED',
    test: async () => {
      const mock = createMockGithub({
        reviews: [
          { user: { login: 'alice' }, state: 'APPROVED', submitted_at: '2026-01-01T00:00:00Z' },
          { user: { login: 'alice' }, state: 'CHANGES_REQUESTED', submitted_at: '2026-01-02T00:00:00Z' },
        ],
      });
      const states = await getLatestReviewStates(mock, 'o', 'r', 1);
      return states.get('alice') === 'CHANGES_REQUESTED';
    },
  },
  {
    name: 'getLatestReviewStates: multiple reviewers tracked independently',
    test: async () => {
      const mock = createMockGithub({
        reviews: [
          { user: { login: 'alice' }, state: 'APPROVED', submitted_at: '2026-01-01T00:00:00Z' },
          { user: { login: 'bob' }, state: 'CHANGES_REQUESTED', submitted_at: '2026-01-02T00:00:00Z' },
        ],
      });
      const states = await getLatestReviewStates(mock, 'o', 'r', 1);
      return states.size === 2 && states.get('alice') === 'APPROVED' && states.get('bob') === 'CHANGES_REQUESTED';
    },
  },
  {
    name: 'getLatestReviewStates: no reviews → empty map',
    test: async () => {
      const mock = createMockGithub({ reviews: [] });
      const states = await getLatestReviewStates(mock, 'o', 'r', 1);
      return states.size === 0;
    },
  },
  {
    name: 'getLatestReviewStates: null login or state gracefully skipped',
    test: async () => {
      const mock = createMockGithub({
        reviews: [
          { user: null, state: 'APPROVED', submitted_at: '2026-01-01T00:00:00Z' },
          { user: { login: 'bob' }, state: null, submitted_at: '2026-01-02T00:00:00Z' },
        ],
      });
      const states = await getLatestReviewStates(mock, 'o', 'r', 1);
      return states.size === 0;
    },
  },
  {
    name: 'getLatestReviewStates: out-of-order timestamps sorted correctly',
    test: async () => {
      const mock = createMockGithub({
        reviews: [
          { user: { login: 'alice' }, state: 'APPROVED', submitted_at: '2026-01-05T00:00:00Z' },
          { user: { login: 'alice' }, state: 'CHANGES_REQUESTED', submitted_at: '2026-01-01T00:00:00Z' },
        ],
      });
      const states = await getLatestReviewStates(mock, 'o', 'r', 1);
      // After sorting, CHANGES_REQUESTED is first, APPROVED is second → final state is APPROVED
      return states.get('alice') === 'APPROVED';
    },
  },
];

async function runUnitTests() {
  console.log('🔬 UNIT TESTS (reviews)');
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

runTestSuite('REVIEWS TEST SUITE', [], async () => true, [
  { label: 'Unit Tests', run: runUnitTests },
]);
