// SPDX-License-Identifier: Apache-2.0
//
// tests/reviews.test.js

const { createMockGithub } = require('./test-utils');
const { getLatestReviewStates } = require('../../review-sync/helpers/reviews');

describe('getLatestReviewStates', () => {
  test('single APPROVED returns approved', async () => {
    const mock = createMockGithub({
      reviews: [
        {
          user: { login: 'alice' },
          state: 'APPROVED',
          submitted_at: '2026-01-01T00:00:00Z',
        },
      ],
    });

    const states = await getLatestReviewStates(mock, 'o', 'r', 1);

    expect(states.size).toBe(1);
    expect(states.get('alice')).toBe('APPROVED');
  });

  test('DISMISSED deletes prior APPROVED', async () => {
    const mock = createMockGithub({
      reviews: [
        {
          user: { login: 'alice' },
          state: 'APPROVED',
          submitted_at: '2026-01-01T00:00:00Z',
        },
        {
          user: { login: 'alice' },
          state: 'DISMISSED',
          submitted_at: '2026-01-02T00:00:00Z',
        },
      ],
    });

    const states = await getLatestReviewStates(mock, 'o', 'r', 1);

    expect(states.size).toBe(0);
  });

  test('COMMENTED is ignored', async () => {
    const mock = createMockGithub({
      reviews: [
        {
          user: { login: 'bob' },
          state: 'COMMENTED',
          submitted_at: '2026-01-01T00:00:00Z',
        },
      ],
    });

    const states = await getLatestReviewStates(mock, 'o', 'r', 1);

    expect(states.size).toBe(0);
  });

  test('later APPROVED overwrites CHANGES_REQUESTED', async () => {
    const mock = createMockGithub({
      reviews: [
        {
          user: { login: 'alice' },
          state: 'CHANGES_REQUESTED',
          submitted_at: '2026-01-01T00:00:00Z',
        },
        {
          user: { login: 'alice' },
          state: 'APPROVED',
          submitted_at: '2026-01-02T00:00:00Z',
        },
      ],
    });

    const states = await getLatestReviewStates(mock, 'o', 'r', 1);

    expect(states.get('alice')).toBe('APPROVED');
  });

  test('later CHANGES_REQUESTED overwrites APPROVED', async () => {
    const mock = createMockGithub({
      reviews: [
        {
          user: { login: 'alice' },
          state: 'APPROVED',
          submitted_at: '2026-01-01T00:00:00Z',
        },
        {
          user: { login: 'alice' },
          state: 'CHANGES_REQUESTED',
          submitted_at: '2026-01-02T00:00:00Z',
        },
      ],
    });

    const states = await getLatestReviewStates(mock, 'o', 'r', 1);

    expect(states.get('alice')).toBe('CHANGES_REQUESTED');
  });

  test('multiple reviewers tracked independently', async () => {
    const mock = createMockGithub({
      reviews: [
        {
          user: { login: 'alice' },
          state: 'APPROVED',
          submitted_at: '2026-01-01T00:00:00Z',
        },
        {
          user: { login: 'bob' },
          state: 'CHANGES_REQUESTED',
          submitted_at: '2026-01-02T00:00:00Z',
        },
      ],
    });

    const states = await getLatestReviewStates(mock, 'o', 'r', 1);

    expect(states.size).toBe(2);
    expect(states.get('alice')).toBe('APPROVED');
    expect(states.get('bob')).toBe('CHANGES_REQUESTED');
  });

  test('no reviews returns empty map', async () => {
    const mock = createMockGithub({
      reviews: [],
    });

    const states = await getLatestReviewStates(mock, 'o', 'r', 1);

    expect(states.size).toBe(0);
  });

  test('null login or state gracefully skipped', async () => {
    const mock = createMockGithub({
      reviews: [
        {
          user: null,
          state: 'APPROVED',
          submitted_at: '2026-01-01T00:00:00Z',
        },
        {
          user: { login: 'bob' },
          state: null,
          submitted_at: '2026-01-02T00:00:00Z',
        },
      ],
    });

    const states = await getLatestReviewStates(mock, 'o', 'r', 1);

    expect(states.size).toBe(0);
  });

  test('out-of-order timestamps sorted correctly', async () => {
    const mock = createMockGithub({
      reviews: [
        {
          user: { login: 'alice' },
          state: 'APPROVED',
          submitted_at: '2026-01-05T00:00:00Z',
        },
        {
          user: { login: 'alice' },
          state: 'CHANGES_REQUESTED',
          submitted_at: '2026-01-01T00:00:00Z',
        },
      ],
    });

    const states = await getLatestReviewStates(mock, 'o', 'r', 1);

    expect(states.get('alice')).toBe('APPROVED');
  });
});
