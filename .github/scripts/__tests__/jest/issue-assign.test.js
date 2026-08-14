//
// Run from .github/scripts:
//
// npm run test:js -- issue-assign.test.js
//

jest.mock('../../shared/api/github-api', () => ({
  getOpenAssignments: jest.fn(),
  countCompletedIssuesWithLabel: jest.fn(),
  isRepoCollaborator: jest.fn(),
  postIssueComment: jest.fn(),
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
  isSpamBlockedLevel: jest.fn(),
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
          login: 'parv',
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
  githubApi.postIssueComment.mockResolvedValue();
  githubApi.assignIssue.mockResolvedValue();

  spam.isSpamUser.mockReturnValue(false);
  spam.isSpamBlockedLevel.mockReturnValue(false);
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
    expect(githubApi.postIssueComment).not.toHaveBeenCalled();
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
    expect(githubApi.postIssueComment).not.toHaveBeenCalled();
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
    expect(githubApi.postIssueComment).not.toHaveBeenCalled();
  });

  test('returns when comment user is missing', async () => {
    const github = createGithub();

    const context = createContext({
      comment: {
        body: '/assign',
      },
    });

    await runAssignmentFlow({ github, context });

    expect(githubApi.assignIssue).not.toHaveBeenCalled();
    expect(githubApi.postIssueComment).not.toHaveBeenCalled();
  });

  test('returns for empty comments', async () => {
    const github = createGithub();

    const context = createContext({
      comment: {
        body: '',
        user: {
          login: 'parv',
          type: 'User',
        },
      },
    });

    await runAssignmentFlow({ github, context });

    expect(githubApi.assignIssue).not.toHaveBeenCalled();
    expect(githubApi.postIssueComment).not.toHaveBeenCalled();
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

    await expect(
      runAssignmentFlow({ github, context })
    ).rejects.toThrow(
      '[assign-bot] Issue #15 has no recognized skill label.'
    );
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
    expect(githubApi.postIssueComment).not.toHaveBeenCalled();
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
          login: 'parv',
          type: 'User',
        },
      },
    });

    await runAssignmentFlow({ github, context });

    expect(githubApi.isRepoCollaborator).toHaveBeenCalledWith({
      github,
      owner: 'hiero-ledger',
      repo: 'hiero-sdk-python',
      username: 'parv',
    });

    expect(githubApi.fetchAllComments).toHaveBeenCalled();

    expect(githubApi.postIssueComment).toHaveBeenCalledTimes(1);

    expect(githubApi.postIssueComment).toHaveBeenCalledWith(
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
          login: 'parv',
          type: 'User',
        },
      },
    });

    await runAssignmentFlow({ github, context });

    expect(githubApi.isRepoCollaborator).not.toHaveBeenCalled();
    expect(githubApi.fetchAllComments).not.toHaveBeenCalled();
    expect(githubApi.postIssueComment).not.toHaveBeenCalled();
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
    expect(githubApi.postIssueComment).not.toHaveBeenCalled();
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
          login: 'parv',
          type: 'User',
        },
      },
    });

    await runAssignmentFlow({ github, context });

    expect(githubApi.fetchAllComments).toHaveBeenCalled();

    expect(githubApi.postIssueComment).not.toHaveBeenCalled();
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
          login: 'parv',
          type: 'User',
        },
      },
    });

    await runAssignmentFlow({ github, context });

    expect(githubApi.fetchAllComments).toHaveBeenCalled();

    expect(githubApi.postIssueComment).not.toHaveBeenCalled();
    expect(githubApi.assignIssue).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// Prerequisites, spam and assignment limits
// ---------------------------------------------------------------------------

describe('runAssignmentFlow - prerequisites', () => {
  test('posts prerequisite guard comment when user has not completed enough issues', async () => {
    githubApi.countCompletedIssuesWithLabel.mockResolvedValue(0);

    const github = createGithub();

    const context = createContext({
      issue: {
        number: 20,
        assignees: [],
        labels: [
          {
            name: 'skill: intermediate',
          },
        ],
      },
    });

    await runAssignmentFlow({ github, context });

    expect(githubApi.countCompletedIssuesWithLabel).toHaveBeenCalled();

    expect(githubApi.postIssueComment).toHaveBeenCalledWith(
      expect.objectContaining({
        owner: 'hiero-ledger',
        repo: 'hiero-sdk-python',
        issueNumber: 20,
        body: '<!-- guard -->\nguard comment',
      }),
      'prerequisite guard'
    );

    expect(githubApi.assignIssue).not.toHaveBeenCalled();
  });

  test('continues when prerequisite lookup fails open', async () => {
    githubApi.countCompletedIssuesWithLabel.mockResolvedValue(null);

    const github = createGithub();

    const context = createContext({
      issue: {
        number: 20,
        assignees: [],
        labels: [
          {
            name: 'skill: intermediate',
          },
        ],
      },
    });

    await runAssignmentFlow({ github, context });

    expect(githubApi.countCompletedIssuesWithLabel).toHaveBeenCalled();

    expect(githubApi.postIssueComment).not.toHaveBeenCalled();

    expect(githubApi.assignIssue).toHaveBeenCalled();
  });

  test('does not post duplicate prerequisite guard comment', async () => {
    githubApi.countCompletedIssuesWithLabel.mockResolvedValue(0);

    githubApi.fetchAllComments.mockResolvedValue([
      {
        body: '<!-- guard -->\nAlready posted.',
      },
    ]);

    const github = createGithub();

    const context = createContext({
      issue: {
        number: 20,
        assignees: [],
        labels: [
          {
            name: 'skill: intermediate',
          },
        ],
      },
    });

    await runAssignmentFlow({ github, context });

    expect(githubApi.fetchAllComments).toHaveBeenCalled();

    expect(githubApi.postIssueComment).not.toHaveBeenCalled();
    expect(githubApi.assignIssue).not.toHaveBeenCalled();
  });

  test('continues when prerequisites are satisfied', async () => {
    githubApi.countCompletedIssuesWithLabel.mockResolvedValue(10);

    const github = createGithub();
    const context = createContext();

    await runAssignmentFlow({ github, context });

    expect(githubApi.countCompletedIssuesWithLabel).toHaveBeenCalled();
    expect(githubApi.assignIssue).toHaveBeenCalled();
  });
});

describe('runAssignmentFlow - spam protection', () => {
  test('blocks permanently banned users', async () => {
    spam.isSpamUser.mockReturnValue(true);
    spam.isSpamBlockedLevel.mockReturnValue(true);

    const github = createGithub();
    const context = createContext();

    await runAssignmentFlow({ github, context });

    expect(githubApi.postIssueComment).toHaveBeenCalledWith(
      expect.objectContaining({
        body: 'spam blocked',
      }),
      "spam restriction notice"
    );

    expect(githubApi.assignIssue).not.toHaveBeenCalled();
  });

  test('posts spam-limited assignment limit comment for restricted users', async () => {
    spam.isSpamUser.mockReturnValue(true);
    spam.isSpamBlockedLevel.mockReturnValue(false);
    spam.isSpamLimited.mockReturnValue(true);
    spam.getAssignmentLimit.mockReturnValue(2);

    githubApi.getOpenAssignments.mockResolvedValue(2);

    const github = createGithub();
    const context = createContext();

    await runAssignmentFlow({ github, context });

    expect(spam.getAssignmentLimit).toHaveBeenCalled();
    expect(spam.isSpamLimited).toHaveBeenCalled();

    expect(githubApi.postIssueComment).toHaveBeenCalledWith(
      expect.objectContaining({
        body: 'limit comment',
      }),
      'limit warning'
    );

    expect(githubApi.assignIssue).not.toHaveBeenCalled();
  });
  test('continues when user is not flagged as spam', async () => {
    spam.isSpamUser.mockReturnValue(false);

    const github = createGithub();
    const context = createContext();

    await runAssignmentFlow({ github, context });

    expect(githubApi.assignIssue).toHaveBeenCalled();
  });
});

describe('runAssignmentFlow - assignment limits', () => {
  test('posts limit comment when user exceeds assignment limit', async () => {
    githubApi.getOpenAssignments.mockResolvedValue(5);
    spam.getAssignmentLimit.mockReturnValue(5);

    const github = createGithub();
    const context = createContext();

    await runAssignmentFlow({ github, context });

    expect(githubApi.postIssueComment).toHaveBeenCalledWith(
      expect.objectContaining({
        body: 'limit comment',
      }),
      'limit warning'
    );

    expect(githubApi.assignIssue).not.toHaveBeenCalled();
  });

  test('allows assignment when user is below assignment limit', async () => {
    githubApi.getOpenAssignments.mockResolvedValue(2);
    spam.getAssignmentLimit.mockReturnValue(5);

    const github = createGithub();
    const context = createContext();

    await runAssignmentFlow({ github, context });

    expect(githubApi.assignIssue).toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// Assignment and error handling
// ---------------------------------------------------------------------------

describe('runAssignmentFlow - assignment', () => {
  test('posts already assigned comment when user already has an open assignment', async () => {

    const github = createGithub();
    const context = createContext({
    issue: {
        number: 10,
        assignees: [{ login: "someone" }],
        labels: [{ name: "skill: beginner" }]
      }
    });

    await runAssignmentFlow({ github, context });

    expect(githubApi.postIssueComment).toHaveBeenCalledWith(
      expect.objectContaining({
        owner: 'hiero-ledger',
        repo: 'hiero-sdk-python',
        issueNumber: 10,
        body: 'already assigned',
      }),
      'already-assigned notice'
    );

    expect(githubApi.assignIssue).not.toHaveBeenCalled();
  });

  test('assigns issue when all checks pass', async () => {
    githubApi.getOpenAssignments.mockResolvedValue(0);

    const github = createGithub();
    const context = createContext();

    await runAssignmentFlow({ github, context });

    expect(githubApi.assignIssue).toHaveBeenCalledWith({
      github,
      owner: 'hiero-ledger',
      repo: 'hiero-sdk-python',
      issueNumber: 10,
      username: 'parv',
    });

    expect(githubApi.postIssueComment).not.toHaveBeenCalled();
  });
});

describe('runAssignmentFlow - error handling', () => {
  test('does not assign when counting completed issues throws', async () => {
    githubApi.countCompletedIssuesWithLabel.mockRejectedValue(
      new Error('Database unavailable')
    );

    const github = createGithub();
    const context = createContext();

    await expect(
      runAssignmentFlow({ github, context })
    ).rejects.toThrow('Database unavailable');

    expect(githubApi.assignIssue).not.toHaveBeenCalled();
  });

  test("continues when assignment lookup fails open", async () => {
    githubApi.getOpenAssignments.mockResolvedValue(null);

    const github = createGithub();
    const context = createContext();

    await runAssignmentFlow({ github, context });

    expect(githubApi.assignIssue).toHaveBeenCalled();
  });

  test('returns when repository owner is missing', async () => {
    const github = createGithub();

    const context = createContext({
      repository: {
        owner: {},
        name: 'hiero-sdk-python',
      },
    });

    await runAssignmentFlow({ github, context });

    expect(githubApi.assignIssue).not.toHaveBeenCalled();
    expect(githubApi.postIssueComment).not.toHaveBeenCalled();
  });

  test('attempts to assign the issue even when assignment fails', async () => {
    githubApi.assignIssue.mockRejectedValue(
      new Error('Assignment failed')
    );

    const github = createGithub();
    const context = createContext();

    await runAssignmentFlow({
        github,
        context
    });

    expect(githubApi.assignIssue).toHaveBeenCalled();
  });

  test('propagates post comment errors', async () => {
    githubApi.postIssueComment.mockRejectedValue(
      new Error('Comment failed')
    );

    githubApi.countCompletedIssuesWithLabel.mockResolvedValue(0);

    const github = createGithub();

    const context = createContext({
      issue: {
        number: 42,
        assignees: [],
        labels: [
          {
            name: 'skill: intermediate',
          },
        ],
      },
    });

    await expect(
      runAssignmentFlow({ github, context })
    ).rejects.toThrow('Comment failed');

    expect(githubApi.assignIssue).not.toHaveBeenCalled();
  });
});
