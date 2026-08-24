// __tests__/jest/review-sync-drafts.test.js
//
// Run from .github/scripts:
// npm run test:js -- review-sync-drafts.test.js
//
// Covers the draft-cleanup path of the Review Queue Label Sync cron job
// (index.js steps 1, 2, 3, 5, 6): rate-limit guard, fetching + splitting
// open PRs into draft/non-draft, and stripping managed labels off drafts.
// Non-draft syncLabel logic itself is covered by labels.test.js.

const { createMockGithub } = require('./test-utils');
const reviewSync = require('../../review-sync');
const { COMMUNITY_REVIEW, QUEUE_LABELS } = require('../../review-sync/helpers/constants');

function createContext() {
  return { repo: { owner: 'o', repo: 'r' } };
}

function createCore() {
  return { setFailed: jest.fn() };
}

function draftPr(number, labelNames) {
  return {
    number,
    draft: true,
    labels: labelNames.map((name) => ({ name })),
    head: { sha: `sha${number}` },
    user: { type: 'User' },
  };
}

function nonDraftPr(number, labelNames = []) {
  return {
    number,
    draft: false,
    labels: labelNames.map((name) => ({ name })),
    head: { sha: `sha${number}` },
    user: { type: 'User' },
  };
}

describe('review-sync draft cleanup (index.js)', () => {
  afterEach(() => {
    delete process.env.DRY_RUN;
  });

  test('cleans managed labels off every draft PR', async () => {
    const mock = createMockGithub({
      existingLabels: {
        [QUEUE_LABELS.JUNIOR.name]: true,
        [QUEUE_LABELS.COMMITTERS.name]: true,
        [QUEUE_LABELS.MAINTAINERS.name]: true,
        [QUEUE_LABELS.MERGE.name]: true,
        [COMMUNITY_REVIEW.name]: true,
      },
      prList: [
        draftPr(1, ['queue:junior-committer', COMMUNITY_REVIEW.name]),
        draftPr(2, ['queue:committers']),
      ],
    });
    const core = createCore();

    await reviewSync({ github: mock, context: createContext(), core });

    expect(mock.calls.labelsRemoved).toEqual(
      expect.arrayContaining(['queue:junior-committer', COMMUNITY_REVIEW.name, 'queue:committers'])
    );
    expect(core.setFailed).not.toHaveBeenCalled();
  });

  test('draft with no managed labels → no removals, no error', async () => {
    const mock = createMockGithub({
      existingLabels: { [COMMUNITY_REVIEW.name]: true },
      prList: [draftPr(3, ['some-unrelated-label'])],
    });
    const core = createCore();

    await reviewSync({ github: mock, context: createContext(), core });

    expect(mock.calls.labelsRemoved).toHaveLength(0);
    expect(core.setFailed).not.toHaveBeenCalled();
  });

  test('mixed draft + non-draft PRs → only the draft is stripped', async () => {
    const mock = createMockGithub({
      roles: {},
      reviews: [],
      existingLabels: {},
      prList: [draftPr(4, ['queue:maintainers']), nonDraftPr(5)],
    });
    const core = createCore();

    await reviewSync({ github: mock, context: createContext(), core });

    expect(mock.calls.labelsRemoved).toContain('queue:maintainers');
    expect(mock.calls.labelsAdded).toContain('queue:junior-committer');
  });

  test('404 on draft label removal → tolerated, run succeeds', async () => {
    const mock = createMockGithub({
      existingLabels: {},
      removeLabelNotFound: ['queue:committers'],
      prList: [draftPr(6, ['queue:committers'])],
    });
    const core = createCore();

    await reviewSync({ github: mock, context: createContext(), core });

    expect(mock.calls.labelsRemoved).not.toContain('queue:committers');
    expect(core.setFailed).not.toHaveBeenCalled();
  });

  test('non-404 removal error on a draft → reported via setFailed', async () => {
    const mock = createMockGithub({
      existingLabels: {},
      removeLabelServerError: ['queue:maintainers'],
      prList: [draftPr(7, ['queue:maintainers'])],
    });
    const core = createCore();

    await reviewSync({ github: mock, context: createContext(), core });

    expect(core.setFailed).toHaveBeenCalledWith(expect.stringContaining('1 error(s)'));
  });

  test('dry run → logs only, no draft labels removed', async () => {
    process.env.DRY_RUN = 'true';
    const mock = createMockGithub({
      existingLabels: {},
      prList: [draftPr(8, ['queue:committers'])],
    });
    const core = createCore();

    await reviewSync({ github: mock, context: createContext(), core });

    expect(mock.calls.labelsRemoved).toHaveLength(0);
  });

  test('rate limit below floor → skips entirely, nothing fetched', async () => {
    const mock = createMockGithub({ prList: [draftPr(9, ['queue:committers'])] });
    mock.rest.rateLimit.get = async () => ({
      data: { resources: { core: { remaining: 10 } } },
    });
    const core = createCore();

    await reviewSync({ github: mock, context: createContext(), core });

    expect(mock.calls.labelsRemoved).toHaveLength(0);
    expect(mock.calls.labelsChecked).toHaveLength(0);
  });

  test('no open PRs at all → exits without ensuring labels', async () => {
    const mock = createMockGithub({ prList: [] });
    const core = createCore();

    await reviewSync({ github: mock, context: createContext(), core });

    expect(mock.calls.labelsChecked).toHaveLength(0);
  });
});
