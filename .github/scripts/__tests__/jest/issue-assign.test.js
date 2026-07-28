//
// Run from .github/scripts:
//
// npm run test:js -- issue-assign.test.js
//

jest.mock('../../shared/api/github-api', () => ({
  getOpenAssignments: jest.fn(),
  countCompletedIssuesWithLabel: jest.fn(),
  isRepoCollaborator: jest.fn(),
  postComment: jest.fn(),
  fetchAllComments: jest.fn(),
  assignIssue: jest.fn(),
}));

jest.mock('../../shared/helpers/comment', () => ({
  buildAlreadyAssignedComment: jest.fn(() => 'already assigned'),
  buildGuardComment: jest.fn(() => 'guard comment'),
  buildLimitComment: jest.fn(() => 'limit comment'),
  buildReminderComment: jest.fn(() => 'reminder comment'),
  buildSpamBlockedComment: jest.fn(() => 'spam blocked'),
  reminderMarkerFor: jest.fn(() => '<!-- reminder -->'),
  guardMarkerFor: jest.fn(() => '<!-- guard -->'),
}));

jest.mock('../../shared/helpers/spam', () => ({
  isSpamUser: jest.fn(),
  spamUsersBlocked: jest.fn(),
  isSpamLimited: jest.fn(),
  getAssignmentLimit: jest.fn(),
}));

const { runAssignmentFlow } = require('../../shared/core/issue-assign');

const githubApi = require('../../shared/api/github-api');
const spam = require('../../shared/helpers/spam');

function createContext(overrides = {}) {
  return {
    payload: {
      repository: {
        owner: {
          login: 'hiero-ledger',
        },
        name: 'hiero-sdk-python',
      },

      issue: {
        number: 10,
        assignees: [],
        labels: [
          {
            name: 'skill: beginner',
          },
        ],
      },

      comment: {
        body: '/assign',
        user: {
          login: 'alice',
          type: 'User',
        },
      },

      ...overrides,
    },
  };
}

function createGithub() {
  return {};
}

beforeEach(() => {
  jest.clearAllMocks();

  githubApi.getOpenAssignments.mockResolvedValue(0);
  githubApi.countCompletedIssuesWithLabel.mockResolvedValue(100);
  githubApi.isRepoCollaborator.mockResolvedValue(false);
  githubApi.fetchAllComments.mockResolvedValue([]);
  githubApi.postComment.mockResolvedValue();
  githubApi.assignIssue.mockResolvedValue();

  spam.isSpamUser.mockReturnValue(false);
  spam.spamUsersBlocked.mockReturnValue(false);
  spam.isSpamLimited.mockReturnValue(false);
  spam.getAssignmentLimit.mockReturnValue(5);
});

describe('runAssignmentFlow - validation', () => {
  test('returns when payload has no issue', async () => {
    const github = createGithub();

    await runAssignmentFlow({
      github,
      context: {
        payload: {},
      },
    });

    expect(githubApi.assignIssue).not.toHaveBeenCalled();
    expect(githubApi.postComment).not.toHaveBeenCalled();
  });

  test('returns for pull request comments', async () => {
    const github = createGithub();

    const context = createContext({
      issue: {
        pull_request: {},
      },
    });

    await runAssignmentFlow({ github, context });

    expect(githubApi.assignIssue).not.toHaveBeenCalled();
    expect(githubApi.postComment).not.toHaveBeenCalled();
  });

  test('returns for bot comments', async () => {
    const github = createGithub();

    const context = createContext({
      comment: {
        body: '/assign',
        user: {
          login: 'dependabot',
          type: 'Bot',
        },
      },
    });

    await runAssignmentFlow({ github, context });

    expect(githubApi.assignIssue).not.toHaveBeenCalled();
    expect(githubApi.postComment).not.toHaveBeenCalled();
  });

  test('returns for empty comments', async () => {
    const github = createGithub();

    const context = createContext({
      comment: {
        body: '',
        user: {
          login: 'alice',
          type: 'User',
        },
      },
    });

    await runAssignmentFlow({ github, context });

    expect(githubApi.assignIssue).not.toHaveBeenCalled();
    expect(githubApi.postComment).not.toHaveBeenCalled();
  });

  test('returns for issues without a recognized skill label', async () => {
    const github = createGithub();

    const context = createContext({
      issue: {
        number: 15,
        assignees: [],
        labels: [
          {
            name: 'documentation',
          },
        ],
      },
    });

    await runAssignmentFlow({ github, context });

    expect(githubApi.assignIssue).not.toHaveBeenCalled();
    expect(githubApi.postComment).not.toHaveBeenCalled();
  });

  test('returns for repositories that are not configured', async () => {
    const github = createGithub();

    const context = createContext({
      repository: {
        owner: {
          login: 'unknown-org',
        },
        name: 'unknown-repo',
      },
    });

    await runAssignmentFlow({ github, context });

    expect(githubApi.assignIssue).not.toHaveBeenCalled();
    expect(githubApi.postComment).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// Reminder flow
// ---------------------------------------------------------------------------

describe('runAssignmentFlow - reminder flow', () => {
  test('posts a reminder for a normal comment on an unassigned issue', async () => {
    const github = createGithub();

    const context = createContext({
      comment: {
        body: 'I would like to work on this!',
        user: {
          login: 'alice',
          type: 'User',
        },
      },
    });

    await runAssignmentFlow({ github, context });

    expect(githubApi.isRepoCollaborator).toHaveBeenCalledWith({
      github,
      owner: 'hiero-ledger',
      repo: 'hiero-sdk-python',
      username: 'alice',
    });

    expect(githubApi.fetchAllComments).toHaveBeenCalled();

    expect(githubApi.postComment).toHaveBeenCalledTimes(1);

    expect(githubApi.postComment).toHaveBeenCalledWith(
      expect.objectContaining({
        owner: 'hiero-ledger',
        repo: 'hiero-sdk-python',
        issueNumber: 10,
        body: '<!-- reminder -->\nreminder comment',
      }),
      'assign reminder'
    );

    expect(githubApi.assignIssue).not.toHaveBeenCalled();
  });

  test('does not post reminder when issue is already assigned', async () => {
    const github = createGithub();

    const context = createContext({
      issue: {
        number: 10,
        assignees: [
          {
            login: 'bob',
          },
        ],
        labels: [
          {
            name: 'skill: beginner',
          },
        ],
      },

      comment: {
        body: 'Interested!',
        user: {
          login: 'alice',
          type: 'User',
        },
      },
    });

    await runAssignmentFlow({ github, context });

    expect(githubApi.isRepoCollaborator).not.toHaveBeenCalled();
    expect(githubApi.fetchAllComments).not.toHaveBeenCalled();
    expect(githubApi.postComment).not.toHaveBeenCalled();
  });

  test('does not post reminder for repository collaborators', async () => {
    githubApi.isRepoCollaborator.mockResolvedValue(true);

    const github = createGithub();

    const context = createContext({
      comment: {
        body: 'Looks interesting',
        user: {
          login: 'maintainer',
          type: 'User',
        },
      },
    });

    await runAssignmentFlow({ github, context });

    expect(githubApi.isRepoCollaborator).toHaveBeenCalled();

    expect(githubApi.fetchAllComments).not.toHaveBeenCalled();
    expect(githubApi.postComment).not.toHaveBeenCalled();
    expect(githubApi.assignIssue).not.toHaveBeenCalled();
  });

  test('does not post duplicate reminder when marker already exists', async () => {
    githubApi.fetchAllComments.mockResolvedValue([
      {
        body: '<!-- reminder -->\nAlready reminded.',
      },
    ]);

    const github = createGithub();

    const context = createContext({
      comment: {
        body: 'Can I work on this?',
        user: {
          login: 'alice',
          type: 'User',
        },
      },
    });

    await runAssignmentFlow({ github, context });

    expect(githubApi.fetchAllComments).toHaveBeenCalled();

    expect(githubApi.postComment).not.toHaveBeenCalled();
    expect(githubApi.assignIssue).not.toHaveBeenCalled();
  });

  test('returns when fetching comments throws during reminder check', async () => {
    githubApi.fetchAllComments.mockRejectedValue(
      new Error('GitHub API unavailable')
    );

    const github = createGithub();

    const context = createContext({
      comment: {
        body: 'Interested',
        user: {
          login: 'alice',
          type: 'User',
        },
      },
    });

    await runAssignmentFlow({ github, context });

    expect(githubApi.fetchAllComments).toHaveBeenCalled();

    expect(githubApi.postComment).not.toHaveBeenCalled();
    expect(githubApi.assignIssue).not.toHaveBeenCalled();
  });
});
