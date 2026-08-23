// __tests__/jest/post-comment.test.js
//
// Run from .github/scripts:
// npm run test:js -- post-comment.test.js

const { postComment } = require('../../shared/helpers/pr-helpers');

function createMockGithub({ shouldFail = false, errorMessage = 'API error' } = {}) {
  const calls = {
    createComment: [],
  };

  const github = {
    calls,
    rest: {
      issues: {
        createComment: jest.fn(async ({ owner, repo, issue_number, body }) => {
          calls.createComment.push({ owner, repo, issue_number, body });
          if (shouldFail) {
            throw new Error(errorMessage);
          }
          return { data: { id: 101 } };
        }),
      },
    },
  };

  return github;
}

function createMockCore() {
  return {
    info: jest.fn(),
    error: jest.fn(),
    warning: jest.fn(),
    setFailed: jest.fn(),
  };
}

describe('postComment helper', () => {
  test('happy path: returns true and logs info when createComment resolves', async () => {
    const github = createMockGithub();
    const core = createMockCore();
    const owner = 'hiero-ledger';
    const repo = 'hiero-sdk-python';
    const prNumber = 123;
    const body = 'Great work on this PR!';

    const result = await postComment(github, owner, repo, prNumber, body, core);

    expect(result).toBe(true);
    expect(github.rest.issues.createComment).toHaveBeenCalledTimes(1);
    expect(github.rest.issues.createComment).toHaveBeenCalledWith({
      owner,
      repo,
      issue_number: prNumber,
      body,
    });
    expect(core.info).toHaveBeenCalledTimes(1);
    expect(core.info).toHaveBeenCalledWith(`Posted recommendation comment to PR #${prNumber}`);
    expect(core.error).not.toHaveBeenCalled();
  });

  test('failure path: returns false, logs error, and does not throw when createComment rejects', async () => {
    const errorMessage = 'Network error: 500 Internal Server Error';
    const github = createMockGithub({ shouldFail: true, errorMessage });
    const core = createMockCore();
    const owner = 'hiero-ledger';
    const repo = 'hiero-sdk-python';
    const prNumber = 456;
    const body = 'Recommendation comment';

    let result;
    let thrownError = null;

    try {
      result = await postComment(github, owner, repo, prNumber, body, core);
    } catch (err) {
      thrownError = err;
    }

    expect(thrownError).toBeNull();
    expect(result).toBe(false);
    expect(github.rest.issues.createComment).toHaveBeenCalledTimes(1);
    expect(github.rest.issues.createComment).toHaveBeenCalledWith({
      owner,
      repo,
      issue_number: prNumber,
      body,
    });
    expect(core.error).toHaveBeenCalledTimes(1);
    expect(core.error).toHaveBeenCalledWith(`Failed to post comment: ${errorMessage}`);
    expect(core.info).not.toHaveBeenCalled();
  });
});
