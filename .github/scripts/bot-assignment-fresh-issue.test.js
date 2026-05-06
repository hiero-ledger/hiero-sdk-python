// Regression coverage for stale issue_comment payloads: the bots must refetch issue state before assigning.

const { describe, it } = require('node:test');
const assert = require('node:assert/strict');

const runGfiAssignBot = require('./bot-gfi-assign-on-comment.js');
const runBeginnerAssignBot = require('./bot-beginner-assign-on-comment.js');

function createContext({ labelName, payloadAssignees = [], freshAssignees = [] }) {
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
        labels: [{ name: labelName }],
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
      labels: [{ name: labelName }],
      assignees: freshAssignees,
    },
  };
}

function createGithubMock(context) {
  const calls = {
    comments: [],
    assignees: [],
  };

  const github = {
    rest: {
      issues: {
        get: async () => ({ data: context.freshIssue }),
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

describe('assignment bots use fresh issue state before assigning', () => {
  it('GFI bot does not assign when webhook payload is stale but issue is now assigned', async () => {
    const context = createContext({
      labelName: 'Good First Issue',
      payloadAssignees: [],
      freshAssignees: [{ login: 'current-assignee' }],
    });
    const { github, calls } = createGithubMock(context);

    await runGfiAssignBot({ github, context });

    assert.equal(calls.assignees.length, 0);
    assert.equal(calls.comments.length, 1);
    assert.match(calls.comments[0].body, /already assigned/i);
    assert.match(calls.comments[0].body, /@current-assignee/);
  });

  it('beginner bot does not assign when webhook payload is stale but issue is now assigned', async () => {
    const context = createContext({
      labelName: 'skill: beginner',
      payloadAssignees: [],
      freshAssignees: [{ login: 'current-assignee' }],
    });
    const { github, calls } = createGithubMock(context);

    await runBeginnerAssignBot({ github, context });

    assert.equal(calls.assignees.length, 0);
    assert.equal(calls.comments.length, 1);
    assert.match(calls.comments[0].body, /already assigned/i);
    assert.match(calls.comments[0].body, /@current-assignee/);
  });
});
