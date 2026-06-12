// __tests__/jest/labels.test.js
//
// Run from .github/scripts:
// npm run test:js -- labels.test.js

const { createMockGithub } = require('./test-utils');
const {
  determineLabel,
  ensureLabel,
  syncLabel,
} = require('../../review-sync/helpers/labels');
const {
  QUEUE_LABELS,
  COMMUNITY_REVIEW,
} = require('../../review-sync/helpers/constants');

describe('determineLabel', () => {
  test('0 approvals → queue:junior-committer', () => {
    const result = determineLabel({
      maintainerApprovals: 0,
      coreApprovals: 0,
      softApprovals: 0,
      anyApproval: 0,
    });

    expect(result.name).toBe('queue:junior-committer');
  });

  test('1 soft approval → queue:committers', () => {
    const result = determineLabel({
      maintainerApprovals: 0,
      coreApprovals: 0,
      softApprovals: 1,
      anyApproval: 1,
    });

    expect(result.name).toBe('queue:committers');
  });

  test('1 write approval → queue:maintainers', () => {
    const result = determineLabel({
      maintainerApprovals: 0,
      coreApprovals: 1,
      softApprovals: 0,
      anyApproval: 1,
    });

    expect(result.name).toBe('queue:maintainers');
  });

  test('2 write + 0 maintainer → queue:maintainers', () => {
    const result = determineLabel({
      maintainerApprovals: 0,
      coreApprovals: 2,
      softApprovals: 0,
      anyApproval: 2,
    });

    expect(result.name).toBe('queue:maintainers');
  });

  test('1 maintainer alone → queue:committers', () => {
    const result = determineLabel({
      maintainerApprovals: 1,
      coreApprovals: 1,
      softApprovals: 0,
      anyApproval: 1,
    });

    expect(result.name).toBe('queue:committers');
  });

  test('1 maintainer + 1 write → status: ready-to-merge', () => {
    const result = determineLabel({
      maintainerApprovals: 1,
      coreApprovals: 2,
      softApprovals: 0,
      anyApproval: 2,
    });

    expect(result.name).toBe('status: ready-to-merge');
  });

  test('1 maintainer + 1 soft → queue:committers', () => {
    const result = determineLabel({
      maintainerApprovals: 1,
      coreApprovals: 1,
      softApprovals: 1,
      anyApproval: 2,
    });

    expect(result.name).toBe('queue:committers');
  });

  test('3 soft approvals → queue:committers', () => {
    const result = determineLabel({
      maintainerApprovals: 0,
      coreApprovals: 0,
      softApprovals: 3,
      anyApproval: 3,
    });

    expect(result.name).toBe('queue:committers');
  });

  test('fully approved but ciFailing=true → queue:junior-committer', () => {
    const result = determineLabel(
      {
        maintainerApprovals: 1,
        coreApprovals: 2,
        softApprovals: 0,
        anyApproval: 2,
      },
      true
    );

    expect(result.name).toBe('queue:junior-committer');
  });
});

describe('ensureLabel', () => {
  test('creates label when missing', async () => {
    const mock = createMockGithub({
      existingLabels: {},
    });

    await ensureLabel(
      mock,
      'o',
      'r',
      QUEUE_LABELS.JUNIOR,
      false
    );

    expect(mock.calls.labelsCreated).toHaveLength(1);
    expect(mock.calls.labelsCreated[0].name)
      .toBe('queue:junior-committer');
  });

  test('skips when label exists', async () => {
    const mock = createMockGithub({
      existingLabels: {
        'queue:junior-committer': true,
      },
    });

    await ensureLabel(
      mock,
      'o',
      'r',
      QUEUE_LABELS.JUNIOR,
      false
    );

    expect(mock.calls.labelsCreated).toHaveLength(0);
  });

  test('dry run does not create', async () => {
    const mock = createMockGithub({
      existingLabels: {},
    });

    await ensureLabel(
      mock,
      'o',
      'r',
      QUEUE_LABELS.JUNIOR,
      true
    );

    expect(mock.calls.labelsCreated).toHaveLength(0);
  });
});

describe('syncLabel', () => {
  test('no approvals, no labels → adds junior-committer', async () => {
    const mock = createMockGithub({
      roles: {},
      reviews: [],
    });

    const changed = await syncLabel(
      mock,
      'o',
      'r',
      {
        number: 1,
        labels: [],
        head: { sha: '123' },
        user: { type: 'User' },
      },
      false
    );

    expect(changed).toBe(true);
    expect(mock.calls.labelsAdded[0])
      .toBe('queue:junior-committer');
  });

  test('already correct, no stale → returns false', async () => {
    const mock = createMockGithub({
      roles: {},
      reviews: [],
    });

    const changed = await syncLabel(
      mock,
      'o',
      'r',
      {
        number: 1,
        labels: [
          { name: 'queue:junior-committer' },
          { name: COMMUNITY_REVIEW.name },
        ],
        head: { sha: '123' },
        user: { type: 'Bot' },
      },
      false
    );

    expect(changed).toBe(false);
    expect(mock.calls.labelsAdded).toHaveLength(0);
  });

  test('stale label → adds correct, removes stale', async () => {
    const mock = createMockGithub({
      roles: {
        sophie: {
          role_name: 'maintain',
          permission: 'write',
        },
        bob: {
          role_name: 'write',
          permission: 'write',
        },
      },
      reviews: [
        {
          user: { login: 'sophie' },
          state: 'APPROVED',
          submitted_at: '2026-01-01T00:00:00Z',
        },
        {
          user: { login: 'bob' },
          state: 'APPROVED',
          submitted_at: '2026-01-02T00:00:00Z',
        },
      ],
    });

    const changed = await syncLabel(
      mock,
      'o',
      'r',
      {
        number: 1,
        labels: [{ name: 'queue:junior-committer' }],
        head: { sha: '123' },
        user: { type: 'User' },
      },
      false
    );

    expect(changed).toBe(true);
    expect(mock.calls.labelsAdded)
      .toContain('status: ready-to-merge');
    expect(mock.calls.labelsRemoved)
      .toContain('queue:junior-committer');
  });

  test('dry run logs but does not modify', async () => {
    const mock = createMockGithub({
      roles: {},
      reviews: [],
    });

    const changed = await syncLabel(
      mock,
      'o',
      'r',
      {
        number: 1,
        labels: [{ name: 'queue:committers' }],
        head: { sha: '123' },
        user: { type: 'User' },
      },
      true
    );

    expect(changed).toBe(true);
    expect(mock.calls.labelsAdded).toHaveLength(0);
  });

  test('correct + stale present → cleans up stale', async () => {
    const mock = createMockGithub({
      roles: {},
      reviews: [],
    });

    const changed = await syncLabel(
      mock,
      'o',
      'r',
      {
        number: 1,
        labels: [
          { name: 'queue:junior-committer' },
          { name: 'queue:committers' },
        ],
        head: { sha: '123' },
        user: { type: 'User' },
      },
      false
    );

    expect(changed).toBe(true);
    expect(mock.calls.labelsRemoved)
      .toContain('queue:committers');
  });

  test('bot PR receives community review label if missing', async () => {
    const mock = createMockGithub({
      roles: {},
      reviews: [],
    });

    const changed = await syncLabel(
      mock,
      'o',
      'r',
      {
        number: 1,
        labels: [{ name: 'queue:junior-committer' }],
        head: { sha: '123' },
        user: { type: 'Bot' },
      },
      false
    );

    expect(changed).toBe(true);
    expect(mock.calls.labelsAdded)
      .toContain(COMMUNITY_REVIEW.name);
  });

  test('human PR receives community review label if missing', async () => {
    const mock = createMockGithub({
      roles: {},
      reviews: [],
    });

    const changed = await syncLabel(
      mock,
      'o',
      'r',
      {
        number: 1,
        labels: [{ name: 'queue:junior-committer' }],
        head: { sha: '123' },
        user: { type: 'User' },
      },
      false
    );

    expect(changed).toBe(true);
    expect(mock.calls.labelsAdded)
      .toContain(COMMUNITY_REVIEW.name);
  });
});
