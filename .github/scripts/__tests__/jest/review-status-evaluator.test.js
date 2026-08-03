// __tests__/jest/review-status-evaluator.test.js
//
// Run from .github/scripts:
// npm run test:js -- review-status-evaluator.test.js

const {
    getPRLabels,
    getReviewState,
    getDetailedReviews,
    computeStatus,
    formatStatusForLog,
    evaluateReviewStatus,
} = require('../../review-status-evaluator');

// ---------------------------------------------------------------------------
// Local mock GitHub client
// ---------------------------------------------------------------------------
// The shared createMockGithub() in test-utils.js doesn't support
// paginate.iterator (async iterator) or graphql, both of which this module
// relies on, so a lightweight local mock is used instead.
//
// Supports multi-page responses via labelPages / reviewPages (each an array
// of pages, where each page is an array of items) so tests can verify that
// getPRLabels and getDetailedReviews actually aggregate across pages rather
// than only ever seeing a single response. `labels` / `reviews` remain as
// convenience shorthands for a single page.

function createMockGithub({
    labels = [],
    labelPages = null,
    reviewDecision = null,
    reviews = [],
    reviewPages = null,
    graphqlError = null,
    labelsError = null,
    reviewsError = null,
} = {}) {
    const resolvedLabelPages = labelPages || [labels];
    const resolvedReviewPages = reviewPages || [reviews];

    return {
        rest: {
            issues: {
                listLabelsOnIssue: async ({ page = 1 } = {}) => {
                    if (labelsError) throw labelsError;
                    const pageItems = resolvedLabelPages[page - 1] || [];
                    return { data: pageItems.map((name) => ({ name })) };
                },
            },
            pulls: {
                listReviews: async ({ page = 1 } = {}) => {
                    if (reviewsError) throw reviewsError;
                    return { data: resolvedReviewPages[page - 1] || [] };
                },
            },
        },
        paginate: {
            // Mirrors Octokit's real iterator: keeps requesting incrementing
            // page numbers until a page comes back empty.
            iterator: (fn, opts) => {
                return (async function* () {
                    let page = 1;
                    while (true) {
                        const response = await fn({ ...opts, page });
                        const isEmpty = !response.data || response.data.length === 0;

                        if (isEmpty) {
                            if (page === 1) yield response; // real API still yields an empty first page
                            break;
                        }

                        yield response;
                        page += 1;
                    }
                })();
            },
        },
        graphql: async () => {
            if (graphqlError) throw graphqlError;
            return {
                repository: {
                    pullRequest: {
                        reviewDecision,
                    },
                },
            };
        },
    };
}

// ---------------------------------------------------------------------------
// getPRLabels
// ---------------------------------------------------------------------------

describe('getPRLabels', () => {
    test('returns label names from paginated REST response', async () => {
        const github = createMockGithub({ labels: ['skill: beginner', 'bug'] });
        const labels = await getPRLabels(github, 'o', 'r', 1);
        expect(labels).toEqual(['skill: beginner', 'bug']);
    });

    test('returns empty array when PR has no labels', async () => {
        const github = createMockGithub({ labels: [] });
        const labels = await getPRLabels(github, 'o', 'r', 1);
        expect(labels).toEqual([]);
    });

    test('returns empty array and does not throw when the API call fails', async () => {
        const github = createMockGithub({ labelsError: new Error('boom') });
        const labels = await getPRLabels(github, 'o', 'r', 1);
        expect(labels).toEqual([]);
    });

    test('aggregates labels across multiple pages', async () => {
        const github = createMockGithub({
            labelPages: [
                ['skill: beginner', 'bug'],
                ['help wanted'],
            ],
        });

        const labels = await getPRLabels(github, 'o', 'r', 1);

        expect(labels).toEqual(['skill: beginner', 'bug', 'help wanted']);
    });
});

// ---------------------------------------------------------------------------
// getReviewState
// ---------------------------------------------------------------------------

describe('getReviewState', () => {
    test('returns reviewDecision from GraphQL response', async () => {
        const github = createMockGithub({ reviewDecision: 'APPROVED' });
        const decision = await getReviewState(github, 'o', 'r', 1);
        expect(decision).toBe('APPROVED');
    });

    test('returns null when reviewDecision is absent', async () => {
        const github = createMockGithub({ reviewDecision: null });
        const decision = await getReviewState(github, 'o', 'r', 1);
        expect(decision).toBeNull();
    });

    test('returns null and does not throw when GraphQL call fails', async () => {
        const github = createMockGithub({ graphqlError: new Error('boom') });
        const decision = await getReviewState(github, 'o', 'r', 1);
        expect(decision).toBeNull();
    });
});

// ---------------------------------------------------------------------------
// getDetailedReviews
// ---------------------------------------------------------------------------

describe('getDetailedReviews', () => {
    test('returns one entry per reviewer using their latest review', async () => {
        const github = createMockGithub({
            reviews: [
                { user: { login: 'alice' }, state: 'CHANGES_REQUESTED', submitted_at: '2026-01-01T00:00:00Z' },
                { user: { login: 'alice' }, state: 'APPROVED', submitted_at: '2026-01-02T00:00:00Z' },
                { user: { login: 'bob' }, state: 'COMMENTED', submitted_at: '2026-01-01T00:00:00Z' },
            ],
        });

        const reviews = await getDetailedReviews(github, 'o', 'r', 1);
        const byReviewer = Object.fromEntries(reviews.map((r) => [r.reviewer, r.state]));

        expect(reviews).toHaveLength(2);
        expect(byReviewer.alice).toBe('APPROVED');
        expect(byReviewer.bob).toBe('COMMENTED');
    });

    test('returns empty array when there are no reviews', async () => {
        const github = createMockGithub({ reviews: [] });
        const reviews = await getDetailedReviews(github, 'o', 'r', 1);
        expect(reviews).toEqual([]);
    });

    test('returns empty array and does not throw when the API call fails', async () => {
        const github = createMockGithub({ reviewsError: new Error('boom') });
        const reviews = await getDetailedReviews(github, 'o', 'r', 1);
        expect(reviews).toEqual([]);
    });

    test('aggregates reviews across multiple pages, keeping the latest per reviewer even when it lands on a later page', async () => {
        const github = createMockGithub({
            reviewPages: [
                [{ user: { login: 'alice' }, state: 'CHANGES_REQUESTED', submitted_at: '2026-01-01T00:00:00Z' }],
                [
                    { user: { login: 'alice' }, state: 'APPROVED', submitted_at: '2026-01-02T00:00:00Z' },
                    { user: { login: 'bob' }, state: 'COMMENTED', submitted_at: '2026-01-01T00:00:00Z' },
                ],
            ],
        });

        const reviews = await getDetailedReviews(github, 'o', 'r', 1);
        const byReviewer = Object.fromEntries(reviews.map((r) => [r.reviewer, r.state]));

        expect(reviews).toHaveLength(2);
        expect(byReviewer.alice).toBe('APPROVED'); // alice's latest review is on page 2
        expect(byReviewer.bob).toBe('COMMENTED');
    });
});

// ---------------------------------------------------------------------------
// computeStatus
// ---------------------------------------------------------------------------

describe('computeStatus', () => {
    test('APPROVED reviewDecision → approved stage, nothing waiting', () => {
        const status = computeStatus(['skill: intermediate'], 'APPROVED', [
            { reviewer: 'alice', state: 'APPROVED', submittedAt: '2026-01-01T00:00:00Z' },
        ]);

        expect(status.currentStage).toBe('approved');
        expect(status.waitingOn).toEqual([]);
    });

    test('CHANGES_REQUESTED reviewDecision → changes_requested stage, full expected list outstanding', () => {
        const status = computeStatus(['skill: advanced'], 'CHANGES_REQUESTED', [
            { reviewer: 'alice', state: 'CHANGES_REQUESTED', submittedAt: '2026-01-01T00:00:00Z' },
        ]);

        expect(status.currentStage).toBe('changes_requested');
        expect(status.waitingOn).toEqual(['committer', 'maintainer']);
    });

    test('no reviewDecision, GFI label, zero approvals → awaiting_triage stage', () => {
        const status = computeStatus(['Good First Issue'], null, []);

        expect(status.currentStage).toBe('awaiting_triage');
        expect(status.waitingOn).toEqual(['triage', 'committer']);
    });

    test('no reviewDecision, GFI label, one approval → awaiting_review stage (triage gate cleared)', () => {
        const status = computeStatus(['skill: beginner'], 'REVIEW_REQUIRED', [
            { reviewer: 'alice', state: 'APPROVED', submittedAt: '2026-01-01T00:00:00Z' },
        ]);

        expect(status.currentStage).toBe('awaiting_review');
        expect(status.waitingOn).toEqual(['committer']);
    });

    test('no reviewDecision, no skill labels → awaiting_review stage, committer+maintainer expected', () => {
        const status = computeStatus([], null, []);

        expect(status.currentStage).toBe('awaiting_review');
        expect(status.expectedReviewers).toEqual(['committer', 'maintainer']);
        expect(status.waitingOn).toEqual(['committer', 'maintainer']);
    });

    test('all expected reviewers have approved → waitingOn is empty even without formal reviewDecision', () => {
        const status = computeStatus(
            ['skill: intermediate'],
            'REVIEW_REQUIRED',
            [
                { reviewer: 'alice', state: 'APPROVED', submittedAt: '2026-01-01T00:00:00Z' },
                { reviewer: 'bob', state: 'APPROVED', submittedAt: '2026-01-02T00:00:00Z' },
            ]
        );

        expect(status.waitingOn).toEqual([]);
    });

    test('summary combines currentStage and nextAction', () => {
        const status = computeStatus([], 'APPROVED', []);
        expect(status.summary).toContain('approved');
        expect(status.summary).toContain(status.nextAction);
    });
});

// ---------------------------------------------------------------------------
// formatStatusForLog
// ---------------------------------------------------------------------------

describe('formatStatusForLog', () => {
    test('includes review status, expected reviewers, waiting on, and next action lines', () => {
        const status = computeStatus(['skill: advanced'], 'CHANGES_REQUESTED', []);
        const formatted = formatStatusForLog(status);

        expect(formatted).toContain('Review status:');
        expect(formatted).toContain('Expected reviewers:');
        expect(formatted).toContain('Waiting on:');
        expect(formatted).toContain('Next action:');
    });

    test('renders "none" for empty waitingOn', () => {
        const status = computeStatus([], 'APPROVED', []);
        const formatted = formatStatusForLog(status);
        expect(formatted).toContain('Waiting on: none');
    });
});

// ---------------------------------------------------------------------------
// evaluateReviewStatus (orchestration)
// ---------------------------------------------------------------------------

describe('evaluateReviewStatus', () => {
    test('returns null when no PR number is found', async () => {
        const github = createMockGithub({});
        const context = { payload: {}, repo: { owner: 'o', repo: 'r' } };

        delete process.env.PR_NUMBER;
        const status = await evaluateReviewStatus(github, context);

        expect(status).toBeNull();
    });

    test('resolves PR number from context.payload.pull_request and returns computed status', async () => {
        const github = createMockGithub({
            labels: ['skill: intermediate'],
            reviewDecision: 'APPROVED',
            reviews: [{ user: { login: 'alice' }, state: 'APPROVED', submitted_at: '2026-01-01T00:00:00Z' }],
        });
        const context = {
            payload: { pull_request: { number: 42 } },
            repo: { owner: 'o', repo: 'r' },
        };

        const status = await evaluateReviewStatus(github, context);

        expect(status).not.toBeNull();
        expect(status.currentStage).toBe('approved');
    });

    test('falls back to PR_NUMBER env var when payload has no pull_request', async () => {
        const github = createMockGithub({ labels: [], reviewDecision: null, reviews: [] });
        const context = { payload: {}, repo: { owner: 'o', repo: 'r' } };

        process.env.PR_NUMBER = '7';
        const status = await evaluateReviewStatus(github, context);
        delete process.env.PR_NUMBER;

        expect(status).not.toBeNull();
    });
});
