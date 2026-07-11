describe('assignment bots use fresh issue state before assigning', () => {
  let runGfiAssignBot;
  let runBeginnerAssignBot;

  beforeAll(() => {
    runGfiAssignBot = require('../../bot-gfi-assign-on-comment.js');
    runBeginnerAssignBot = require('../../bot-beginner-assign-on-comment.js');
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  function createContext({ labelName, payloadAssignees = [], freshLabels, freshAssignees = [], freshState = 'open' }) {
    const labels = [{ name: labelName }];

    return {
      repo: {
        owner: 'hiero-ledger',
        repo: 'hiero-sdk-python',
      },
      payload: {
        repository: {
          owner: { login: 'hiero-ledger' },
          name: 'hiero-sdk-python',
        },
        issue: {
          number: 123,
          labels,
          assignees: payloadAssignees,
        },
        comment: {
          body: '/assign',
          user: {
            login: 'new-contributor',
            type: 'User',
          },
        },
      },
      freshIssue: {
        number: 123,
        title: 'Example issue',
        state: freshState,
        labels: freshLabels ?? labels,
        assignees: freshAssignees,
      },
    };
  }

  function createGithubMock(context, { freshIssueError } = {}) {
    const calls = {
      comments: [],
      assignees: [],
    };

    const github = {
      rest: {
        issues: {
          get: async () => {
            if (freshIssueError) {
              throw freshIssueError;
            }
            return { data: context.freshIssue };
          },
          createComment: async (params) => {
            calls.comments.push(params);
            return { data: {} };
          },
          addAssignees: async (params) => {
            calls.assignees.push(params);
            return { data: {} };
          },
        },
      },
      paginate: async () => [],
      graphql: async () => ({ search: { issueCount: 1 } }),
    };

    return { github, calls };
  }

  it('GFI bot does not assign when webhook payload is stale but issue is now assigned', async () => {
    const context = createContext({
      labelName: 'Good First Issue',
      payloadAssignees: [],
      freshAssignees: [{ login: 'current-assignee' }],
    });
    const { github, calls } = createGithubMock(context);

    await runGfiAssignBot({ github, context });

    expect(calls.assignees.length).toBe(0);
    expect(calls.comments.length).toBe(1);
    expect(calls.comments[0].body).toMatch(/already assigned/i);
    expect(calls.comments[0].body).toMatch(/@current-assignee/);
  });

  it('GFI bot exits safely when fresh issue fetch fails before assignment', async () => {
    const context = createContext({
      labelName: 'Good First Issue',
      payloadAssignees: [],
    });
    const { github, calls } = createGithubMock(context, {
      freshIssueError: Object.assign(new Error('GitHub API unavailable'), { status: 503 }),
    });

    await runGfiAssignBot({ github, context });

    expect(calls.assignees.length).toBe(0);
    expect(calls.comments.length).toBe(0);
  });

  it('GFI bot exits when the fresh issue is no longer a Good First Issue', async () => {
    const context = createContext({
      labelName: 'Good First Issue',
      payloadAssignees: [],
      freshLabels: [{ name: 'help wanted' }],
    });
    const { github, calls } = createGithubMock(context);

    await runGfiAssignBot({ github, context });

    expect(calls.assignees.length).toBe(0);
    expect(calls.comments.length).toBe(0);
  });

  it('GFI bot exits when the fresh issue is closed before assignment', async () => {
    const context = createContext({
      labelName: 'Good First Issue',
      payloadAssignees: [],
      freshState: 'closed',
    });
    const { github, calls } = createGithubMock(context);

    await runGfiAssignBot({ github, context });

    expect(calls.assignees.length).toBe(0);
    expect(calls.comments.length).toBe(0);
  });

  it('beginner bot does not assign when webhook payload is stale but issue is now assigned', async () => {
    const context = createContext({
      labelName: 'skill: beginner',
      payloadAssignees: [],
      freshAssignees: [{ login: 'current-assignee' }],
    });
    const { github, calls } = createGithubMock(context);

    await runBeginnerAssignBot({ github, context });

    expect(calls.assignees.length).toBe(0);
    expect(calls.comments.length).toBe(1);
    expect(calls.comments[0].body).toMatch(/already assigned/i);
    expect(calls.comments[0].body).toMatch(/@current-assignee/);
  });

  it('beginner bot exits safely when fresh issue fetch fails before assignment', async () => {
    const context = createContext({
      labelName: 'skill: beginner',
      payloadAssignees: [],
    });
    const { github, calls } = createGithubMock(context, {
      freshIssueError: Object.assign(new Error('GitHub API unavailable'), { status: 503 }),
    });

    await runBeginnerAssignBot({ github, context });

    expect(calls.assignees.length).toBe(0);
    expect(calls.comments.length).toBe(0);
  });

  it('beginner bot exits when the fresh issue no longer has the beginner label', async () => {
    const context = createContext({
      labelName: 'skill: beginner',
      payloadAssignees: [],
      freshLabels: [{ name: 'help wanted' }],
    });
    const { github, calls } = createGithubMock(context);

    await runBeginnerAssignBot({ github, context });

    expect(calls.assignees.length).toBe(0);
    expect(calls.comments.length).toBe(0);
  });

  it('beginner bot exits when the fresh issue is closed before assignment', async () => {
    const context = createContext({
      labelName: 'skill: beginner',
      payloadAssignees: [],
      freshState: 'closed',
    });
    const { github, calls } = createGithubMock(context);

    await runBeginnerAssignBot({ github, context });

    expect(calls.assignees.length).toBe(0);
    expect(calls.comments.length).toBe(0);
  });
});
