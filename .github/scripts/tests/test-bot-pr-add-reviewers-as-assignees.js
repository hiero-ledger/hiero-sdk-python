// SPDX-License-Identifier: Apache-2.0

/**
 * @fileoverview
 * Unit tests for the bot-pr-add-reviewers-as-assignees.js script.
 *
 * Tests cover individual reviewers, team ignoring, deduplication, assignee cap,
 * workflow_dispatch support, error handling (403 graceful, 500 rethrow), etc.
 */

const assert = require('assert');
const { createLogger } = require('../helpers/index.js');

const logger = createLogger('test-reviewers-assignee');

/**
 * Creates fresh state for each test to prevent leakage between tests.
 *
 * @returns {Object} Test state object
 */
function createTestState() {
  return {
    addAssigneesCalls: [],
    pullsGetCalls: 0,
    currentPrData: null
  };
}

/**
 * Creates a completely fresh mock GitHub Actions context object for each test.
 *
 * @param {Object} [prData={}] - Optional pull_request data overrides
 * @returns {Object} Fresh context
 */
const createMockContext = (prData = {}) => ({
  repo: { owner: 'hiero-ledger', repo: 'hiero-sdk-python' },
  eventName: 'pull_request_target',
  payload: {
    pull_request: {
      number: 123,
      requested_reviewers: [],
      requested_teams: [],
      assignees: [],
      ...prData
    }
  }
});

/**
 * Creates a properly configured mock GitHub client that returns test-specific PR data.
 *
 * @param {Object} state - Test state containing currentPrData and addAssigneesCalls
 * @returns {Object} Mock GitHub client
 */
function createMockGithub(state) {
  return {
    rest: {
      pulls: {
        get: async ({ pull_number }) => {
          state.pullsGetCalls++;
          return {
            data: {
              number: pull_number,
              requested_reviewers: state.currentPrData?.requested_reviewers || [],
              requested_teams: state.currentPrData?.requested_teams || [],
              assignees: state.currentPrData?.assignees || []
            }
          };
        }
      },
      issues: {
        addAssignees: async (params) => {
          state.addAssigneesCalls.push(params);
          return { data: {} };
        }
      }
    }
  };
}

/**
 * Creates an error mock for testing error handling paths (403, 500, etc.).
 *
 * @param {number} status - HTTP status code to throw
 * @returns {Object} Mock GitHub client that throws on addAssignees
 */
const createErrorMock = (status) => ({
  rest: {
    pulls: {
      get: async ({ pull_number }) => ({
        data: {
          number: pull_number,
          requested_reviewers: [{ login: 'x' }],
          requested_teams: [],
          assignees: []
        }
      })
    },
    issues: {
      addAssignees: async () => {
        const error = new Error(`Error ${status}`);
        error.status = status;
        throw error;
      }
    }
  }
});

// ==================== Test Cases ====================

/**
 * Test 1: Individual reviewers are correctly added as assignees.
 */
async function testIndividualReviewers(handler) {
  console.log('Test 1: Individual reviewers');
  const state = createTestState();
  state.currentPrData = {
    requested_reviewers: [{ login: 'alice' }, { login: 'bob' }],
    assignees: []
  };

  const ctx = createMockContext({
    number: 123,
    requested_reviewers: [{ login: 'alice' }, { login: 'bob' }],
    assignees: []
  });

  const mockGithub = createMockGithub(state);
  await handler({ github: mockGithub, context: ctx });

  assert.strictEqual(state.addAssigneesCalls.length, 1);
  const call = state.addAssigneesCalls[0];
  assert.strictEqual(call.owner, 'hiero-ledger');
  assert.strictEqual(call.repo, 'hiero-sdk-python');
  assert.strictEqual(call.issue_number, 123);
  assert.deepStrictEqual(call.assignees.sort(), ['alice', 'bob']);
  console.log('✅ Passed');
}

/**
 * Test 2: Teams are ignored (only individual reviewers assigned).
 */
async function testTeamIgnored(handler) {
  console.log('Test 2: Teams ignored');
  const state = createTestState();
  state.currentPrData = {
    requested_reviewers: [{ login: 'charlie' }],
    requested_teams: [{ slug: 'team1' }],
    assignees: []
  };

  const ctx = createMockContext({
    number: 124,
    requested_reviewers: [{ login: 'charlie' }],
    requested_teams: [{ slug: 'team1' }]
  });

  const mockGithub = createMockGithub(state);
  await handler({ github: mockGithub, context: ctx });

  assert.strictEqual(state.addAssigneesCalls.length, 1);
  const call = state.addAssigneesCalls[0];
  assert.deepStrictEqual(call.assignees, ['charlie']);
  console.log('✅ Passed');
}

/**
 * Test 3: Deduplication against existing assignees.
 */
async function testDeduplication(handler) {
  console.log('Test 3: Deduplication');
  const state = createTestState();
  state.currentPrData = {
    requested_reviewers: [{ login: 'alice' }],
    assignees: [{ login: 'alice' }]
  };

  const ctx = createMockContext({
    number: 125,
    requested_reviewers: [{ login: 'alice' }],
    assignees: [{ login: 'alice' }]
  });

  const mockGithub = createMockGithub(state);
  await handler({ github: mockGithub, context: ctx });

  assert.strictEqual(state.addAssigneesCalls.length, 0);
  console.log('✅ Passed');
}

/**
 * Test 4: Cap at MAX_ASSIGNEES = 2.
 */
async function testCapAtTwo(handler) {
  console.log('Test 4: Cap at 2');
  const state = createTestState();
  state.currentPrData = {
    requested_reviewers: [{ login: 'u1' }, { login: 'u2' }, { login: 'u3' }],
    assignees: []
  };

  const ctx = createMockContext({
    number: 126,
    requested_reviewers: [{ login: 'u1' }, { login: 'u2' }, { login: 'u3' }]
  });

  const mockGithub = createMockGithub(state);
  await handler({ github: mockGithub, context: ctx });

  assert.strictEqual(state.addAssigneesCalls.length, 1, 'Expected exactly one addAssignees call');
  const call = state.addAssigneesCalls[0];
  assert.strictEqual(call.owner, 'hiero-ledger');
  assert.strictEqual(call.repo, 'hiero-sdk-python');
  assert.strictEqual(call.issue_number, 126);
  assert.strictEqual(call.assignees.length, 2);
  console.log('✅ Passed');
}

/**
 * Test 5: workflow_dispatch with pr_number input.
 */
async function testWorkflowDispatch(handler) {
  console.log('Test 5: workflow_dispatch');
  const state = createTestState();
  state.currentPrData = { requested_reviewers: [{ login: 'eve' }], assignees: [] };

  const ctx = {
    repo: { owner: 'hiero-ledger', repo: 'hiero-sdk-python' },
    eventName: 'workflow_dispatch',
    payload: { inputs: { pr_number: 128 } }
  };

  const mockGithub = createMockGithub(state);
  await handler({ github: mockGithub, context: ctx });

  assert.strictEqual(state.addAssigneesCalls.length, 1, 'Expected exactly one addAssignees call');
  const call = state.addAssigneesCalls[0];
  assert.strictEqual(call.owner, 'hiero-ledger');
  assert.strictEqual(call.repo, 'hiero-sdk-python');
  assert.strictEqual(call.issue_number, 128);
  assert.deepStrictEqual(call.assignees, ['eve']);
  console.log('✅ Passed');
}

/**
 * Test 6: No reviewers requested (no-op).
 */
async function testNoReviewers(handler) {
  console.log('Test 6: No reviewers');
  const state = createTestState();

  const ctx = createMockContext({
    number: 129,
    requested_reviewers: []
  });

  const mockGithub = createMockGithub(state);
  await handler({ github: mockGithub, context: ctx });

  assert.strictEqual(state.addAssigneesCalls.length, 0);
  console.log('✅ Passed');
}

/**
 * Test 7: Invalid pr_number in workflow_dispatch.
 */
async function testInvalidPrNumber(handler) {
  console.log('Test 7: Invalid PR number on workflow_dispatch');
  const badValues = ['0', '-1', '12.5', 'abc', ''];

  for (const v of badValues) {
    const state = createTestState();
    const ctx = {
      repo: { owner: 'hiero-ledger', repo: 'hiero-sdk-python' },
      eventName: 'workflow_dispatch',
      payload: { inputs: { pr_number: v } }
    };
    await handler({ github: createMockGithub(state), context: ctx });
    assert.strictEqual(state.pullsGetCalls, 0);
    assert.strictEqual(state.addAssigneesCalls.length, 0);
  }
  console.log('✅ Passed');
}

/**
 * Test 8: Team-only request (nothing assigned).
 */
async function testTeamOnly(handler) {
  console.log('Test 8: Team-only request');
  const state = createTestState();
  state.currentPrData = {
    requested_reviewers: [],
    requested_teams: [{ slug: 'team' }]
  };

  const ctx = createMockContext({
    number: 130,
    requested_reviewers: [],
    requested_teams: [{ slug: 'team' }]
  });

  const mockGithub = createMockGithub(state);
  await handler({ github: mockGithub, context: ctx });

  assert.strictEqual(state.addAssigneesCalls.length, 0);
  console.log('✅ Passed');
}

/**
 * Test 9: Partial deduplication.
 */
async function testPartialDeduplication(handler) {
  console.log('Test 9: Partial deduplication');
  const state = createTestState();
  state.currentPrData = {
    requested_reviewers: [{ login: 'alice' }, { login: 'bob' }],
    assignees: [{ login: 'alice' }]
  };

  const ctx = createMockContext({
    number: 131,
    requested_reviewers: [{ login: 'alice' }, { login: 'bob' }],
    assignees: [{ login: 'alice' }]
  });

  const mockGithub = createMockGithub(state);
  await handler({ github: mockGithub, context: ctx });

  assert.strictEqual(state.addAssigneesCalls.length, 1, 'Expected exactly one addAssignees call');
  const call = state.addAssigneesCalls[0];
  assert.deepStrictEqual(call.assignees, ['bob']);
  console.log('✅ Passed');
}

/**
 * Test 10: 403 error handled gracefully.
 */
async function test403Graceful(handler) {
  console.log('Test 10: 403 graceful handling');

  let addAssigneesWasCalled = false;

  const errorMock = {
    rest: {
      pulls: {
        get: async ({ pull_number }) => ({
          data: {
            number: pull_number,
            requested_reviewers: [{ login: 'x' }]
          }
        })
      },
      issues: {
        addAssignees: async () => {
          addAssigneesWasCalled = true;
          const error = new Error('Permission denied');
          error.status = 403;
          throw error;
        }
      }
    }
  };

  const ctx = createMockContext({
    number: 132,
    requested_reviewers: [{ login: 'x' }]
  });

  await handler({ github: errorMock, context: ctx });

  assert.strictEqual(addAssigneesWasCalled, true,
    'addAssignees should have been called before 403 error');

  console.log('✅ Passed (403 was caught and handled gracefully)');
}

/**
 * Test 11: Non-403 errors (e.g. 500) are rethrown.
 */
async function test500Rethrow(handler) {
  console.log('Test 11: 500 should rethrow');

  const ctx = createMockContext({
    number: 133,
    requested_reviewers: [{ login: 'x' }]
  });

  await assert.rejects(
    () => handler({ github: createErrorMock(500), context: ctx }),
    (err) => err.status === 500
  );
  console.log('✅ Passed');
}

async function runTests() {
  console.log('\n🚀 Running tests for bot-pr-add-reviewers-as-assignees.js...\n');

  const handler = require('../bot-pr-add-reviewers-as-assignees.js');

  await testIndividualReviewers(handler);
  await testTeamIgnored(handler);
  await testDeduplication(handler);
  await testCapAtTwo(handler);
  await testWorkflowDispatch(handler);
  await testNoReviewers(handler);
  await testInvalidPrNumber(handler);
  await testTeamOnly(handler);
  await testPartialDeduplication(handler);
  await test403Graceful(handler);
  await test500Rethrow(handler);

  console.log('\n🎉 All 11 tests passed!');
}

runTests().catch(err => {
  console.error('❌ Test failed:', err.message);
  process.exit(1);
});
