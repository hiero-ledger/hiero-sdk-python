const { describe, it, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');

function freshRequire() {
  const indexPath = require.resolve('./index.js');
  const helpersPath = require.resolve('./helpers/index.js');
  const labelsPath = require.resolve('./helpers/labels.js');
  const constantsPath = require.resolve('./helpers/constants.js');
  const draftPath = require.resolve('./helpers/draft.js');

  delete require.cache[indexPath];
  delete require.cache[helpersPath];
  delete require.cache[labelsPath];
  delete require.cache[constantsPath];
  delete require.cache[draftPath];

  return require('./index.js');
}

function createGithubMock() {
  const removedLabels = [];
  const graphqlCalls = [];
  let graphqlError;

  return {
    removedLabels,
    graphqlCalls,
    failGraphql(error) {
      graphqlError = error;
    },
    graphql: async (query, variables) => {
      graphqlCalls.push({ query, variables });
      if (graphqlError) {
        throw graphqlError;
      }
      return {
        convertPullRequestToDraft: {
          pullRequest: {
            id: variables.pullRequestId,
            isDraft: true,
          },
        },
      };
    },
    rest: {
      issues: {
        removeLabel: async ({ name }) => {
          removedLabels.push(name);
        },
      },
    },
  };
}

function createContext(overrides = {}) {
  return {
    repo: { owner: 'hiero-ledger', repo: 'hiero-sdk-python' },
    payload: {
      review: { state: 'changes_requested' },
      pull_request: {
        number: 42,
        node_id: 'PR_node_42',
        draft: false,
        user: { login: 'contributor', type: 'User' },
        labels: [
          { name: 'queue:committers' },
          { name: 'status: ready-to-merge' },
          { name: 'some other label' },
        ],
      },
      ...overrides,
    },
  };
}

describe('revision-guard index', () => {
  beforeEach(() => {
    delete process.env.REVISION_GUARD_MANAGED_LABELS;
    delete process.env.REVIEWBOT_TOKEN;
  });

  afterEach(() => {
    delete process.env.REVISION_GUARD_MANAGED_LABELS;
    delete process.env.REVIEWBOT_TOKEN;
  });

  it('removes only managed labels without draft conversion when no review bot token is configured', async () => {
    const handler = freshRequire();
    const github = createGithubMock();
    const context = createContext();

    await handler({ github, context, core: { info() {} } });

    assert.equal(github.graphqlCalls.length, 0);
    assert.deepEqual(github.removedLabels, [
      'queue:committers',
      'status: ready-to-merge',
    ]);
  });

  it('skips bot-authored PRs', async () => {
    const handler = freshRequire();
    const github = createGithubMock();
    const context = createContext({
      pull_request: {
        number: 43,
        node_id: 'PR_node_43',
        draft: false,
        user: { login: 'github-actions[bot]', type: 'Bot' },
        labels: [{ name: 'queue:committers' }],
      },
    });

    await handler({ github, context, core: { info() {} } });

    assert.equal(github.graphqlCalls.length, 0);
    assert.equal(github.removedLabels.length, 0);
  });

  it('removes managed labels from already-draft PRs without converting again', async () => {
    const handler = freshRequire();
    const github = createGithubMock();
    const context = createContext({
      pull_request: {
        number: 44,
        node_id: 'PR_node_44',
        draft: true,
        user: { login: 'contributor', type: 'User' },
        labels: [{ name: 'queue:committers' }],
      },
    });

    await handler({ github, context, core: { info() {} } });

    assert.equal(github.graphqlCalls.length, 0);
    assert.deepEqual(github.removedLabels, ['queue:committers']);
  });

  it('converts to draft when a review bot token is configured', async () => {
    process.env.REVIEWBOT_TOKEN = 'token';
    const handler = freshRequire();
    const github = createGithubMock();
    const context = createContext();

    await handler({ github, context, core: { info() {} } });

    assert.equal(github.graphqlCalls.length, 1);
    assert.match(github.graphqlCalls[0].query, /convertPullRequestToDraft/);
    assert.deepEqual(github.graphqlCalls[0].variables, { pullRequestId: 'PR_node_42' });
    assert.deepEqual(github.removedLabels, [
      'queue:committers',
      'status: ready-to-merge',
    ]);
  });

  it('still removes managed labels when draft conversion fails', async () => {
    process.env.REVIEWBOT_TOKEN = 'token';
    const handler = freshRequire();
    const github = createGithubMock();
    github.failGraphql(new Error('Resource not accessible by integration'));
    const context = createContext();

    await handler({ github, context, core: { error() {}, info() {} } });

    assert.equal(github.graphqlCalls.length, 1);
    assert.deepEqual(github.removedLabels, [
      'queue:committers',
      'status: ready-to-merge',
    ]);
  });

  it('uses configurable managed labels and still removes defaults', async () => {
    process.env.REVISION_GUARD_MANAGED_LABELS = 'custom: one, custom: two';
    const handler = freshRequire();
    const github = createGithubMock();
    const context = createContext({
      pull_request: {
        number: 45,
        node_id: 'PR_node_45',
        draft: false,
        user: { login: 'contributor', type: 'User' },
        labels: [
          { name: 'custom: one' },
          { name: 'queue:committers' },
          { name: 'custom: two' },
        ],
      },
    });

    await handler({ github, context, core: { info() {} } });

    assert.equal(github.graphqlCalls.length, 0);
    // Custom labels AND the matching default (queue:committers) must both be removed.
    assert.deepEqual(github.removedLabels, ['queue:committers', 'custom: one', 'custom: two']);
  });
});
