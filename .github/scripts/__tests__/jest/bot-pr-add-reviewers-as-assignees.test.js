// __tests__/jest/bot-pr-add-reviewers-as-assignees.test.js
//
// Run from .github/scripts:
// npm run test:js -- bot-pr-add-reviewers-as-assignees.test.js

describe('Bot: Add Reviewers as Assignees', () => {
  let handler;
  let removeReviewerFromAssignees;
  let clearReviewStateOnDraft;

  beforeAll(() => {
    const mod = require('../../bot-pr-add-reviewers-as-assignees.js');
    handler = mod;
    removeReviewerFromAssignees = mod.removeReviewerFromAssignees;
    clearReviewStateOnDraft = mod.clearReviewStateOnDraft;
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  const createTestState = () => ({
    addAssigneesCalls: [],
    removeAssigneesCalls: [],
    removeRequestedReviewersCalls: [],
    pullsGetCalls: 0,
    currentPrData: null,
  });

  const createMockContext = (prData = {}) => ({
    repo: { owner: 'hiero-ledger', repo: 'hiero-sdk-python' },
    eventName: 'pull_request_target',
    payload: {
      action: 'review_requested',
      pull_request: {
        number: 123,
        user: { login: 'author' },
        requested_reviewers: [],
        requested_teams: [],
        assignees: [],
        ...prData
      }
    }
  });

  // Minimal context for remove flow: only repo is required when explicit params are passed
  const minimalContext = { repo: { owner: 'hiero-ledger', repo: 'hiero-sdk-python' } };

  const createMockGithub = (state) => ({
    rest: {
      pulls: {
        get: async ({ pull_number }) => {
          state.pullsGetCalls++;
          return {
            data: {
              number: pull_number,
              draft: state.currentPrData?.draft !== undefined ? state.currentPrData.draft : true,
              user: state.currentPrData?.user || { login: 'author' },
              requested_reviewers: state.currentPrData?.requested_reviewers || [],
              requested_teams: state.currentPrData?.requested_teams || [],
              assignees: state.currentPrData?.assignees || []
            }
          };
        },
        removeRequestedReviewers: async (params) => {
          state.removeRequestedReviewersCalls.push(params);
          return { data: {} };
        }
      },
      issues: {
        addAssignees: async (params) => {
          state.addAssigneesCalls.push(params);
          return { data: {} };
        },
        removeAssignees: async (params) => {
          state.removeAssigneesCalls.push(params);
          return { data: {} };
        }
      }
    }
  });

  // ─── Add flow ────────────────────────────────────────────────────────────────

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

  test('adds all requested reviewers as assignees without cap', async () => {
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
    expect(state.addAssigneesCalls[0].assignees.sort()).toEqual(['u1', 'u2', 'u3']);
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

  test('supports workflow_dispatch with pr_number input and routes to add flow', async () => {
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
    expect(state.removeAssigneesCalls).toHaveLength(0);
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

  test('gracefully handles 403 permission errors on add', async () => {
    const ctx = createMockContext({ requested_reviewers: [{ login: 'x' }] });

    const errorMock = {
      rest: {
        pulls: { get: async () => ({ data: { requested_reviewers: [{ login: 'x' }] } }) },
        issues: {
          addAssignees: async () => {
            const err = new Error('Forbidden');
            err.status = 403;
            throw err;
          },
          removeAssignees: async () => {}
        }
      }
    };

    await expect(handler({ github: errorMock, context: ctx })).resolves.not.toThrow();
  });

  test('rethrows non-403 errors on add', async () => {
    const ctx = createMockContext({ requested_reviewers: [{ login: 'x' }] });

    const errorMock = {
      rest: {
        pulls: { get: async () => ({ data: { requested_reviewers: [{ login: 'x' }] } }) },
        issues: {
          addAssignees: async () => {
            const err = new Error('Internal Server Error');
            err.status = 500;
            throw err;
          },
          removeAssignees: async () => {}
        }
      }
    };

    await expect(handler({ github: errorMock, context: ctx })).rejects.toHaveProperty('status', 500);
  });

  // ─── Remove flow (named export — called from workflow_run job) ────────────────

  test('removes reviewer from assignees when called with explicit params', async () => {
    const state = createTestState();
    state.currentPrData = { assignees: [{ login: 'alice' }, { login: 'bob' }] };

    await removeReviewerFromAssignees({
      github: createMockGithub(state),
      context: minimalContext,
      reviewer: 'alice',
      prNumber: 123
    });

    expect(state.removeAssigneesCalls).toHaveLength(1);
    expect(state.removeAssigneesCalls[0].assignees).toEqual(['alice']);
    expect(state.addAssigneesCalls).toHaveLength(0);
  });

  test('does not remove when reviewer is not an assignee', async () => {
    const state = createTestState();
    state.currentPrData = { assignees: [{ login: 'alice' }] };

    await removeReviewerFromAssignees({
      github: createMockGithub(state),
      context: minimalContext,
      reviewer: 'carol',
      prNumber: 123
    });

    expect(state.removeAssigneesCalls).toHaveLength(0);
  });

  test('is a no-op when reviewer was never an assignee', async () => {
    const state = createTestState();
    state.currentPrData = { assignees: [] };

    await removeReviewerFromAssignees({
      github: createMockGithub(state),
      context: minimalContext,
      reviewer: 'outsider',
      prNumber: 123
    });

    expect(state.removeAssigneesCalls).toHaveLength(0);
  });

  test('skips when reviewer is missing', async () => {
    const state = createTestState();

    await removeReviewerFromAssignees({
      github: createMockGithub(state),
      context: minimalContext,
      reviewer: undefined,
      prNumber: 123
    });

    expect(state.removeAssigneesCalls).toHaveLength(0);
    expect(state.pullsGetCalls).toBe(0);
  });

  test('skips when prNumber is invalid', async () => {
    const state = createTestState();

    await removeReviewerFromAssignees({
      github: createMockGithub(state),
      context: minimalContext,
      reviewer: 'alice',
      prNumber: 0
    });

    expect(state.removeAssigneesCalls).toHaveLength(0);
    expect(state.pullsGetCalls).toBe(0);
  });

  test('skips when reviewer login does not match valid GitHub login pattern', async () => {
    const invalidLogins = ['-starts-with-dash', 'has space', 'has@symbol', ''];

    for (const login of invalidLogins) {
      const state = createTestState();

      await removeReviewerFromAssignees({
        github: createMockGithub(state),
        context: minimalContext,
        reviewer: login,
        prNumber: 123
      });

      expect(state.removeAssigneesCalls).toHaveLength(0);
      expect(state.pullsGetCalls).toBe(0);
    }
  });

  test('gracefully handles 403 permission errors on remove', async () => {
    const errorMock = {
      rest: {
        pulls: { get: async () => ({ data: { assignees: [{ login: 'alice' }] } }) },
        issues: {
          addAssignees: async () => {},
          removeAssignees: async () => {
            const err = new Error('Forbidden');
            err.status = 403;
            throw err;
          }
        }
      }
    };

    await expect(
      removeReviewerFromAssignees({ github: errorMock, context: minimalContext, reviewer: 'alice', prNumber: 123 })
    ).resolves.not.toThrow();
  });

  test('rethrows non-403 errors on remove', async () => {
    const errorMock = {
      rest: {
        pulls: { get: async () => ({ data: { assignees: [{ login: 'alice' }] } }) },
        issues: {
          addAssignees: async () => {},
          removeAssignees: async () => {
            const err = new Error('Internal Server Error');
            err.status = 500;
            throw err;
          }
        }
      }
    };

    await expect(
      removeReviewerFromAssignees({ github: errorMock, context: minimalContext, reviewer: 'alice', prNumber: 123 })
    ).rejects.toHaveProperty('status', 500);
  });

  // ─── Clear review state on draft ─────────────────────────────────────────────

  test('withdraws individual and team review requests and removes reviewer assignees', async () => {
    const state = createTestState();
    state.currentPrData = {
      user: { login: 'author' },
      requested_reviewers: [{ login: 'alice' }, { login: 'bob' }],
      requested_teams: [{ slug: 'team-backend' }],
      assignees: [{ login: 'author' }, { login: 'alice' }, { login: 'bob' }]
    };

    const ctx = createMockContext({ number: 123 });

    await clearReviewStateOnDraft({
      github: createMockGithub(state),
      context: ctx,
      prNumber: 123
    });

    expect(state.removeRequestedReviewersCalls).toHaveLength(1);
    expect(state.removeRequestedReviewersCalls[0]).toEqual({
      owner: 'hiero-ledger',
      repo: 'hiero-sdk-python',
      pull_number: 123,
      reviewers: ['alice', 'bob'],
      team_reviewers: ['team-backend']
    });

    expect(state.removeAssigneesCalls).toHaveLength(1);
    expect(state.removeAssigneesCalls[0]).toEqual({
      owner: 'hiero-ledger',
      repo: 'hiero-sdk-python',
      issue_number: 123,
      assignees: ['alice', 'bob']
    });
  });

  test('skips cleanup when the live PR is not a draft', async () => {
    const state = createTestState();
    state.currentPrData = {
      draft: false,
      requested_reviewers: [{ login: 'alice' }],
      requested_teams: [{ slug: 'team1' }],
      assignees: [{ login: 'alice' }]
    };

    const ctx = createMockContext({ number: 123 });

    await clearReviewStateOnDraft({
      github: createMockGithub(state),
      context: ctx,
      prNumber: 123
    });

    expect(state.removeRequestedReviewersCalls).toHaveLength(0);
    expect(state.removeAssigneesCalls).toHaveLength(0);
  });

  test('withdraws review request when reviewer is not an assignee', async () => {
    const state = createTestState();
    state.currentPrData = {
      requested_reviewers: [{ login: 'alice' }],
      requested_teams: [],
      assignees: []
    };

    const ctx = createMockContext({ number: 123 });

    await clearReviewStateOnDraft({
      github: createMockGithub(state),
      context: ctx,
      prNumber: 123
    });

    expect(state.removeRequestedReviewersCalls).toHaveLength(1);
    expect(state.removeRequestedReviewersCalls[0].reviewers).toEqual(['alice']);
    expect(state.removeAssigneesCalls).toHaveLength(0);
  });

  test('does not remove PR author from assignees', async () => {
    const state = createTestState();
    state.currentPrData = {
      user: { login: 'author' },
      requested_reviewers: [{ login: 'alice' }],
      requested_teams: [],
      assignees: [{ login: 'author' }, { login: 'alice' }]
    };

    const ctx = createMockContext({ number: 123 });

    await clearReviewStateOnDraft({
      github: createMockGithub(state),
      context: ctx,
      prNumber: 123
    });

    expect(state.removeAssigneesCalls).toHaveLength(1);
    expect(state.removeAssigneesCalls[0].assignees).toEqual(['alice']);
    expect(state.removeAssigneesCalls[0].assignees).not.toContain('author');
  });

  test('does nothing when there are no pending review requests', async () => {
    const state = createTestState();
    state.currentPrData = {
      requested_reviewers: [],
      requested_teams: [],
      assignees: [{ login: 'author' }, { login: 'someone-else' }]
    };

    const ctx = createMockContext({ number: 123 });

    await clearReviewStateOnDraft({
      github: createMockGithub(state),
      context: ctx,
      prNumber: 123
    });

    expect(state.removeRequestedReviewersCalls).toHaveLength(0);
    expect(state.removeAssigneesCalls).toHaveLength(0);
  });

  test('continues assignee cleanup even if removeRequestedReviewers returns 403', async () => {
    const state = createTestState();
    const mockGithub = {
      rest: {
        pulls: {
          get: async () => ({
            data: {
              number: 123,
              draft: true,
              user: { login: 'author' },
              requested_reviewers: [{ login: 'alice' }],
              requested_teams: [],
              assignees: [{ login: 'alice' }]
            }
          }),
          removeRequestedReviewers: async (params) => {
            state.removeRequestedReviewersCalls.push(params);
            const err = new Error('Forbidden');
            err.status = 403;
            throw err;
          }
        },
        issues: {
          removeAssignees: async (params) => {
            state.removeAssigneesCalls.push(params);
            return { data: {} };
          }
        }
      }
    };

    await clearReviewStateOnDraft({
      github: mockGithub,
      context: minimalContext,
      prNumber: 123
    });

    expect(state.removeRequestedReviewersCalls).toHaveLength(1);
    expect(state.removeAssigneesCalls).toHaveLength(1);
    expect(state.removeAssigneesCalls[0].assignees).toEqual(['alice']);
  });

  test('tolerates 403 error on removeAssignees', async () => {
    const state = createTestState();
    const mockGithub = {
      rest: {
        pulls: {
          get: async () => ({
            data: {
              number: 123,
              draft: true,
              user: { login: 'author' },
              requested_reviewers: [{ login: 'alice' }],
              requested_teams: [],
              assignees: [{ login: 'alice' }]
            }
          }),
          removeRequestedReviewers: async (params) => {
            state.removeRequestedReviewersCalls.push(params);
            return { data: {} };
          }
        },
        issues: {
          removeAssignees: async (params) => {
            state.removeAssigneesCalls.push(params);
            const err = new Error('Forbidden');
            err.status = 403;
            throw err;
          }
        }
      }
    };

    await expect(
      clearReviewStateOnDraft({
        github: mockGithub,
        context: minimalContext,
        prNumber: 123
      })
    ).resolves.not.toThrow();

    expect(state.removeRequestedReviewersCalls).toHaveLength(1);
    expect(state.removeAssigneesCalls).toHaveLength(1);
  });

  test('gracefully handles 403 permission errors on pulls.get', async () => {
    const errorMock = {
      rest: {
        pulls: {
          get: async () => {
            const err = new Error('Forbidden');
            err.status = 403;
            throw err;
          },
          removeRequestedReviewers: async () => {}
        },
        issues: {
          removeAssignees: async () => {}
        }
      }
    };

    await expect(
      clearReviewStateOnDraft({ github: errorMock, context: minimalContext, prNumber: 123 })
    ).resolves.not.toThrow();
  });

  test('rethrows non-403 errors on clearReviewStateOnDraft', async () => {
    const errorMock = {
      rest: {
        pulls: {
          get: async () => ({
            data: {
              number: 123,
              draft: true,
              requested_reviewers: [{ login: 'alice' }],
              requested_teams: [],
              assignees: [{ login: 'alice' }]
            }
          }),
          removeRequestedReviewers: async () => {
            const err = new Error('Internal Server Error');
            err.status = 500;
            throw err;
          }
        },
        issues: {
          removeAssignees: async () => {}
        }
      }
    };

    await expect(
      clearReviewStateOnDraft({ github: errorMock, context: minimalContext, prNumber: 123 })
    ).rejects.toHaveProperty('status', 500);
  });

  // ─── Routing ─────────────────────────────────────────────────────────────────

  test('unhandled event logs warning and does nothing', async () => {
    const state = createTestState();
    const ctx = {
      repo: { owner: 'hiero-ledger', repo: 'hiero-sdk-python' },
      eventName: 'pull_request_review',
      payload: { action: 'submitted' }
    };

    await handler({ github: createMockGithub(state), context: ctx });

    expect(state.addAssigneesCalls).toHaveLength(0);
    expect(state.removeAssigneesCalls).toHaveLength(0);
  });
});


