const { describe, it, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');

function freshRequire() {
  const indexPath = require.resolve('./index.js');
  const helpersPath = require.resolve('./helpers/index.js');
  const labelsPath = require.resolve('./helpers/labels.js');
  const constantsPath = require.resolve('./helpers/constants.js');

  delete require.cache[indexPath];
  delete require.cache[helpersPath];
  delete require.cache[labelsPath];
  delete require.cache[constantsPath];

  return require('./index.js');
}

function createGithubMock() {
  const removedLabels = [];

  return {
    removedLabels,
    graphqlCalls: [],
    graphql: async function (_query, variables) {
      this.graphqlCalls.push(variables);
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
  });

  afterEach(() => {
    delete process.env.REVISION_GUARD_MANAGED_LABELS;
  });

  it('converts a ready PR to draft and removes only managed labels', async () => {
    const handler = freshRequire();
    const github = createGithubMock();
    const context = createContext();

    await handler({ github, context, core: { info() {} } });

    assert.deepEqual(github.graphqlCalls, [{ pullRequestId: 'PR_node_42' }]);
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

  it('skips already-draft PRs', async () => {
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
    assert.equal(github.removedLabels.length, 0);
  });

  it('uses configurable managed labels', async () => {
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

    assert.deepEqual(github.removedLabels, ['custom: one', 'custom: two']);
  });
});
