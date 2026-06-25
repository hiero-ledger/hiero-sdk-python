// __tests__/jest/permissions.test.js
//
// Run from .github/scripts:
// npm run test:js -- permissions.test.js

const { createMockGithub } = require('./test-utils');
const {
  getPermissionLevel,
  countApprovals,
  clearPermissionCache,
} = require('../../review-sync/helpers/permissions');

beforeEach(() => {
  clearPermissionCache();
});

describe('getPermissionLevel', () => {
  test('uses role_name over permission (maintain case)', async () => {
    const mock = createMockGithub({
      roles: {
        sophie: {
          role_name: 'maintain',
          permission: 'write',
        },
      },
    });

    const result = await getPermissionLevel(
      mock,
      'owner',
      'repo',
      'sophie'
    );

    expect(result).toBe('maintain');
  });

  test('uses role_name over permission (admin case)', async () => {
    const mock = createMockGithub({
      roles: {
        admin: {
          role_name: 'admin',
          permission: 'admin',
        },
      },
    });

    const result = await getPermissionLevel(
      mock,
      'owner',
      'repo',
      'admin'
    );

    expect(result).toBe('admin');
  });

  test('falls back to permission if role_name missing', async () => {
    const mock = createMockGithub({
      roles: {
        bob: {
          permission: 'write',
        },
      },
    });

    const result = await getPermissionLevel(
      mock,
      'owner',
      'repo',
      'bob'
    );

    expect(result).toBe('write');
  });

  test('external contributor (404) returns none', async () => {
    const mock = createMockGithub({
      roles: {},
    });

    const result = await getPermissionLevel(
      mock,
      'owner',
      'repo',
      'unknown-user'
    );

    expect(result).toBe('none');
  });

  test('triage role returned correctly', async () => {
    const mock = createMockGithub({
      roles: {
        triager: {
          role_name: 'triage',
          permission: 'read',
        },
      },
    });

    const result = await getPermissionLevel(
      mock,
      'owner',
      'repo',
      'triager'
    );

    expect(result).toBe('triage');
  });

  test('read role returned correctly', async () => {
    const mock = createMockGithub({
      roles: {
        reader: {
          role_name: 'read',
          permission: 'read',
        },
      },
    });

    const result = await getPermissionLevel(
      mock,
      'owner',
      'repo',
      'reader'
    );

    expect(result).toBe('read');
  });
});

describe('countApprovals', () => {
  test('maintain counted as maintainerApprovals and coreApprovals', async () => {
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

    const result = await countApprovals(
      mock,
      'owner',
      'repo',
      1
    );

    expect(result.maintainerApprovals).toBe(1);
    expect(result.coreApprovals).toBe(2);
    expect(result.softApprovals).toBe(0);
    expect(result.anyApproval).toBe(2);
  });

  test('admin counted as maintainerApprovals and coreApprovals', async () => {
    const mock = createMockGithub({
      roles: {
        admin: {
          role_name: 'admin',
          permission: 'admin',
        },
      },
      reviews: [
        {
          user: { login: 'admin' },
          state: 'APPROVED',
          submitted_at: '2026-01-01T00:00:00Z',
        },
      ],
    });

    const result = await countApprovals(
      mock,
      'owner',
      'repo',
      1
    );

    expect(result.maintainerApprovals).toBe(1);
    expect(result.coreApprovals).toBe(1);
    expect(result.anyApproval).toBe(1);
  });

  test('external contributor counted as softApprovals', async () => {
    const mock = createMockGithub({
      roles: {},
      reviews: [
        {
          user: { login: 'external' },
          state: 'APPROVED',
          submitted_at: '2026-01-01T00:00:00Z',
        },
      ],
    });

    const result = await countApprovals(
      mock,
      'owner',
      'repo',
      1
    );

    expect(result.maintainerApprovals).toBe(0);
    expect(result.coreApprovals).toBe(0);
    expect(result.softApprovals).toBe(1);
    expect(result.anyApproval).toBe(1);
  });

  test('CHANGES_REQUESTED not counted in any counter', async () => {
    const mock = createMockGithub({
      roles: {
        bob: {
          role_name: 'write',
          permission: 'write',
        },
      },
      reviews: [
        {
          user: { login: 'bob' },
          state: 'CHANGES_REQUESTED',
          submitted_at: '2026-01-01T00:00:00Z',
        },
      ],
    });

    const result = await countApprovals(
      mock,
      'owner',
      'repo',
      1
    );

    expect(result.anyApproval).toBe(0);
  });

  test('no reviews returns all zeros', async () => {
    const mock = createMockGithub({
      roles: {},
      reviews: [],
    });

    const result = await countApprovals(
      mock,
      'owner',
      'repo',
      1
    );

    expect(result.maintainerApprovals).toBe(0);
    expect(result.coreApprovals).toBe(0);
    expect(result.softApprovals).toBe(0);
    expect(result.anyApproval).toBe(0);
  });

  test('mixed roles — 1 admin + 1 write + 1 external', async () => {
    const mock = createMockGithub({
      roles: {
        admin: {
          role_name: 'admin',
          permission: 'admin',
        },
        committer: {
          role_name: 'write',
          permission: 'write',
        },
      },
      reviews: [
        {
          user: { login: 'admin' },
          state: 'APPROVED',
          submitted_at: '2026-01-01T00:00:00Z',
        },
        {
          user: { login: 'committer' },
          state: 'APPROVED',
          submitted_at: '2026-01-02T00:00:00Z',
        },
        {
          user: { login: 'random' },
          state: 'APPROVED',
          submitted_at: '2026-01-03T00:00:00Z',
        },
      ],
    });

    const result = await countApprovals(
      mock,
      'owner',
      'repo',
      1
    );

    expect(result.maintainerApprovals).toBe(1);
    expect(result.coreApprovals).toBe(2);
    expect(result.softApprovals).toBe(1);
    expect(result.anyApproval).toBe(3);
  });

  test('DISMISSED approval is not counted', async () => {
    const mock = createMockGithub({
      roles: {
        sophie: {
          role_name: 'maintain',
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
          user: { login: 'sophie' },
          state: 'DISMISSED',
          submitted_at: '2026-01-02T00:00:00Z',
        },
      ],
    });

    const result = await countApprovals(
      mock,
      'owner',
      'repo',
      1
    );

    expect(result.maintainerApprovals).toBe(0);
    expect(result.anyApproval).toBe(0);
  });
});
