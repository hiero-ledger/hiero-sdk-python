// __tests__/jest/bot-pr-add-reviewers-as-assignees.test.js
//
// Run from .github/scripts:
// npm run test:js -- bot-pr-add-reviewers-as-assignees.test.js

describe('Bot: Add Reviewers as Assignees', () => {
  let handler;

  beforeAll(() => {
    handler = require('../../bot-pr-add-reviewers-as-assignees.js');
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  const createTestState = () => ({
    addAssigneesCalls: [],
    pullsGetCalls: 0,
    currentPrData: null,
  });

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

  const createMockGithub = (state) => ({
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
  });

  test('adds individual reviewers correctly as assignees', async () => {
    const state = createTestState();
    state.currentPrData = {
      requested_reviewers: [{ login: 'alice' }, { login: 'bob' }],
      assignees: []
    };

    const ctx = createMockContext({
      requested_reviewers: [{ login: 'alice' }, { login: 'bob' }]
    });

    await handler({ github: createMockGithub(state), context: ctx });

    expect(state.addAssigneesCalls).toHaveLength(1);
    const call = state.addAssigneesCalls[0];
    expect(call.assignees.sort()).toEqual(['alice', 'bob']);
  });

  test('ignores team reviewers', async () => {
    const state = createTestState();
    state.currentPrData = {
      requested_reviewers: [{ login: 'charlie' }],
      requested_teams: [{ slug: 'team1' }],
      assignees: []
    };

    const ctx = createMockContext({
      requested_reviewers: [{ login: 'charlie' }],
      requested_teams: [{ slug: 'team1' }]
    });

    await handler({ github: createMockGithub(state), context: ctx });

    expect(state.addAssigneesCalls).toHaveLength(1);
    expect(state.addAssigneesCalls[0].assignees).toEqual(['charlie']);
  });

  test('skips users who are already assignees (deduplication)', async () => {
    const state = createTestState();
    state.currentPrData = {
      requested_reviewers: [{ login: 'alice' }],
      assignees: [{ login: 'alice' }]
    };

    const ctx = createMockContext({
      requested_reviewers: [{ login: 'alice' }],
      assignees: [{ login: 'alice' }]
    });

    await handler({ github: createMockGithub(state), context: ctx });

    expect(state.addAssigneesCalls).toHaveLength(0);
  });

  test('respects MAX_ASSIGNEES = 2 cap', async () => {
    const state = createTestState();
    state.currentPrData = {
      requested_reviewers: [{ login: 'u1' }, { login: 'u2' }, { login: 'u3' }],
      assignees: []
    };

    const ctx = createMockContext({
      requested_reviewers: [{ login: 'u1' }, { login: 'u2' }, { login: 'u3' }]
    });

    await handler({ github: createMockGithub(state), context: ctx });

    expect(state.addAssigneesCalls).toHaveLength(1);
    expect(state.addAssigneesCalls[0].assignees).toHaveLength(2);
  });

  test('does nothing when no reviewers are requested', async () => {
    const state = createTestState();
    const ctx = createMockContext({ requested_reviewers: [] });

    await handler({ github: createMockGithub(state), context: ctx });

    expect(state.addAssigneesCalls).toHaveLength(0);
  });

  test('does nothing when only team reviewers are requested', async () => {
    const state = createTestState();
    const ctx = createMockContext({
      requested_reviewers: [],
      requested_teams: [{ slug: 'team' }]
    });

    await handler({ github: createMockGithub(state), context: ctx });

    expect(state.addAssigneesCalls).toHaveLength(0);
  });

  test('supports workflow_dispatch with pr_number input', async () => {
    const state = createTestState();
    state.currentPrData = { requested_reviewers: [{ login: 'eve' }], assignees: [] };

    const ctx = {
      repo: { owner: 'hiero-ledger', repo: 'hiero-sdk-python' },
      eventName: 'workflow_dispatch',
      payload: { inputs: { pr_number: 128 } }
    };

    await handler({ github: createMockGithub(state), context: ctx });

    expect(state.addAssigneesCalls).toHaveLength(1);
    expect(state.addAssigneesCalls[0].issue_number).toBe(128);
  });

  test('handles invalid pr_number in workflow_dispatch', async () => {
    const badValues = ['0', '-1', '12.5', 'abc', ''];

    for (const v of badValues) {
      const state = createTestState();
      const ctx = {
        repo: { owner: 'hiero-ledger', repo: 'hiero-sdk-python' },
        eventName: 'workflow_dispatch',
        payload: { inputs: { pr_number: v } }
      };

      await handler({ github: createMockGithub(state), context: ctx });
      expect(state.pullsGetCalls).toBe(0);
      expect(state.addAssigneesCalls).toHaveLength(0);
    }
  });

  test('gracefully handles 403 permission errors', async () => {
    const ctx = createMockContext({ requested_reviewers: [{ login: 'x' }] });

    const errorMock = {
      rest: {
        pulls: { get: async () => ({ data: { requested_reviewers: [{ login: 'x' }] } }) },
        issues: {
          addAssignees: async () => {
            const err = new Error('Forbidden');
            err.status = 403;
            throw err;
          }
        }
      }
    };

    await expect(handler({ github: errorMock, context: ctx })).resolves.not.toThrow();
  });

  test('rethrows non-403 errors', async () => {
    const ctx = createMockContext({ requested_reviewers: [{ login: 'x' }] });

    const errorMock = {
      rest: {
        pulls: { get: async () => ({ data: { requested_reviewers: [{ login: 'x' }] } }) },
        issues: {
          addAssignees: async () => {
            const err = new Error('Internal Server Error');
            err.status = 500;
            throw err;
          }
        }
      }
    };

    await expect(handler({ github: errorMock, context: ctx })).rejects.toHaveProperty('status', 500);
  });
});
