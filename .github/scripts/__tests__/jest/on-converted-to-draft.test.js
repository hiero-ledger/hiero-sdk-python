// __tests__/jest/on-converted-to-draft.test.js
//
// Run from .github/scripts:
// npm run test:js -- on-converted-to-draft.test.js

const { createMockGithub } = require('./test-utils');
const onConvertedToDraft = require('../../review-sync/on-converted-to-draft');
const { COMMUNITY_REVIEW } = require('../../review-sync/helpers/constants');

function createContext(pr) {
  return {
    repo: { owner: 'o', repo: 'r' },
    payload: { pull_request: pr },
  };
}

function createCore() {
  return { setFailed: jest.fn() };
}

describe('on-converted-to-draft', () => {
  afterEach(() => {
    delete process.env.DRY_RUN;
    delete process.env.PR_NUMBER;
  });

  test('draft PR with managed labels → strips them', async () => {
    const mock = createMockGithub({});
    const core = createCore();
    const pr = {
      number: 1,
      draft: true,
      labels: [{ name: 'queue:junior-committer' }, { name: COMMUNITY_REVIEW.name }],
    };

    await onConvertedToDraft({ github: mock, context: createContext(pr), core });

    expect(mock.calls.labelsRemoved).toContain('queue:junior-committer');
    expect(mock.calls.labelsRemoved).toContain(COMMUNITY_REVIEW.name);
    expect(core.setFailed).not.toHaveBeenCalled();
  });

  test('non-draft PR in payload → skips cleanup', async () => {
    const mock = createMockGithub({});
    const core = createCore();
    const pr = {
      number: 2,
      draft: false,
      labels: [{ name: 'queue:committers' }],
    };

    await onConvertedToDraft({ github: mock, context: createContext(pr), core });

    expect(mock.calls.labelsRemoved).toHaveLength(0);
    expect(core.setFailed).not.toHaveBeenCalled();
  });

  test('no pull_request in payload and no PR_NUMBER → setFailed, no fetch', async () => {
    const mock = createMockGithub({});
    const core = createCore();

    await onConvertedToDraft({ github: mock, context: createContext(undefined), core });

    expect(core.setFailed).toHaveBeenCalledWith(
      'No pull_request in payload and no PR_NUMBER provided.'
    );
    expect(mock.calls.pullsFetched).toHaveLength(0);
  });

  test('no pull_request in payload, PR_NUMBER set → fetches PR then cleans', async () => {
    process.env.PR_NUMBER = '7';
    const mock = createMockGithub({
      prData: {
        number: 7,
        draft: true,
        labels: [{ name: 'queue:maintainers' }],
      },
    });
    const core = createCore();

    await onConvertedToDraft({ github: mock, context: createContext(undefined), core });

    expect(mock.calls.pullsFetched).toEqual([7]);
    expect(mock.calls.labelsRemoved).toContain('queue:maintainers');
    expect(core.setFailed).not.toHaveBeenCalled();
  });

  test('pulls.get rejects → setFailed with contextual message, no throw', async () => {
    process.env.PR_NUMBER = '8';
    const mock = createMockGithub({});
    const core = createCore();

    await onConvertedToDraft({ github: mock, context: createContext(undefined), core });

    expect(mock.calls.pullsFetched).toEqual([8]);
    expect(core.setFailed).toHaveBeenCalledWith(
      expect.stringContaining('Failed to clean draft PR #8')
    );
  });

  test('fetched PR is not a draft → skips cleanup', async () => {
    process.env.PR_NUMBER = '9';
    const mock = createMockGithub({
      prData: {
        number: 9,
        draft: false,
        labels: [{ name: 'queue:committers' }],
      },
    });
    const core = createCore();

    await onConvertedToDraft({ github: mock, context: createContext(undefined), core });

    expect(mock.calls.labelsRemoved).toHaveLength(0);
    expect(core.setFailed).not.toHaveBeenCalled();
  });

  test('dry run → does not remove labels', async () => {
    process.env.DRY_RUN = 'true';
    const mock = createMockGithub({});
    const core = createCore();
    const pr = {
      number: 3,
      draft: true,
      labels: [{ name: 'queue:committers' }],
    };

    await onConvertedToDraft({ github: mock, context: createContext(pr), core });

    expect(mock.calls.labelsRemoved).toHaveLength(0);
  });

  test('cleanup failure → setFailed with contextual message', async () => {
    const mock = createMockGithub({
      removeLabelServerError: ['queue:committers'],
    });
    const core = createCore();
    const pr = {
      number: 4,
      draft: true,
      labels: [{ name: 'queue:committers' }],
    };

    await onConvertedToDraft({ github: mock, context: createContext(pr), core });

    expect(core.setFailed).toHaveBeenCalledWith(
      expect.stringContaining('Failed to clean draft PR #4')
    );
  });
});
