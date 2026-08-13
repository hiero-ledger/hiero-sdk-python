// __tests__/jest/review-status-evaluator.test.js
//
// Run from .github/scripts:
// npm run test:js -- review-status-evaluator.test.js

// evaluateReviewStatus() reads the roster via shared/team-roles.js's
// getTeamRoles(), which resolves docs/team.md relative to process.cwd().
// Jest runs from .github/scripts (see package.json's test:js script), so
// the real docs/team.md two directories up wouldn't be found — mock the
// module so evaluateReviewStatus tests exercise fixture roster data
// instead of depending on cwd.
jest.mock('../../shared/team-roles');

const {
    getPRLabels,
    getReviewState,
    getDetailedReviews,
    computeStatus,
    formatStatusForLog,
    resolvePrNumber,
    evaluateReviewStatus,
} = require('../../review-status-evaluator');
const { getTeamRoles } = require('../../shared/team-roles');
const {
    GOOD_FIRST_ISSUE_LABEL,
    BEGINNER_LABEL,
    INTERMEDIATE_LABEL,
    ADVANCED_LABEL,
} = require('../../shared/labels');

// Shared fixture roster, used both directly (passed into computeStatus) and
// via the getTeamRoles() mock (for evaluateReviewStatus's orchestration).
// alice is triage-only, bob is a maintainer (and therefore also qualifies
// for the committer gate, since maintainer is a superset of committer
// authority) — this keeps the triage-vs-committer distinction meaningful
// in tests below.
const testTeamRoles = {
    available: true,
    triage: new Set(['carol', 'alice']),
    committer: new Set(),
    maintainer: new Set(['bob']),
};

const rosterUnavailable = {
    available: false,
    triage: new Set(),
    committer: new Set(),
    maintainer: new Set(),
};

beforeEach(() => {
    getTeamRoles.mockReturnValue(testTeamRoles);
});

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
        const github = createMockGithub({ labels: [BEGINNER_LABEL, 'bug'] });
        const labels = await getPRLabels(github, 'o', 'r', 1);
        expect(labels).toEqual([BEGINNER_LABEL, 'bug']);
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
                [BEGINNER_LABEL, 'bug'],
                ['help wanted'],
            ],
        });

        const labels = await getPRLabels(github, 'o', 'r', 1);

        expect(labels).toEqual([BEGINNER_LABEL, 'bug', 'help wanted']);
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
    test('APPROVED reviewDecision alone does not clear incomplete role gates', () => {
        // GitHub's reviewDecision can flip to "APPROVED" once branch
        // protection's required-approval count is met by *any* reviewer,
        // even one who only qualifies for a lower role than this PR's
        // expected reviewer set needs. alice is triage-only in the fixture
        // roster, so her approval alone must not be enough to satisfy the
        // committer + maintainer gates that 'skill: intermediate' expects.
        const status = computeStatus([INTERMEDIATE_LABEL], 'APPROVED', [
            { reviewer: 'alice', state: 'APPROVED', submittedAt: '2026-01-01T00:00:00Z' },
        ], testTeamRoles);

        expect(status.currentStage).not.toBe('approved');
        expect(status.waitingOn).toEqual(['committer', 'maintainer']);
    });

    test('APPROVED reviewDecision with every expected role qualified → approved stage, nothing waiting', () => {
        // bob is a maintainer in the fixture roster, and maintainer is a
        // superset of committer authority, so bob's single approval clears
        // both roles that 'skill: intermediate' expects.
        const status = computeStatus([INTERMEDIATE_LABEL], 'APPROVED', [
            { reviewer: 'bob', state: 'APPROVED', submittedAt: '2026-01-01T00:00:00Z' },
        ], testTeamRoles);

        expect(status.currentStage).toBe('approved');
        expect(status.waitingOn).toEqual([]);
    });

    test('CHANGES_REQUESTED reviewDecision → changes_requested stage, full expected list outstanding', () => {
        const status = computeStatus([ADVANCED_LABEL], 'CHANGES_REQUESTED', [
            { reviewer: 'alice', state: 'CHANGES_REQUESTED', submittedAt: '2026-01-01T00:00:00Z' },
        ], testTeamRoles);

        expect(status.currentStage).toBe('changes_requested');
        expect(status.waitingOn).toEqual(['committer', 'maintainer']);
    });

    test('no reviewDecision, GFI label, zero approvals → awaiting_triage stage', () => {
        const status = computeStatus([GOOD_FIRST_ISSUE_LABEL], null, [], testTeamRoles);

        expect(status.currentStage).toBe('awaiting_triage');
        expect(status.waitingOn).toEqual(['triage', 'committer']);
    });

    test('no reviewDecision, GFI label, one approval → awaiting_review stage (triage gate cleared)', () => {
        const status = computeStatus([BEGINNER_LABEL], 'REVIEW_REQUIRED', [
            { reviewer: 'alice', state: 'APPROVED', submittedAt: '2026-01-01T00:00:00Z' },
        ], testTeamRoles);

        expect(status.currentStage).toBe('awaiting_review');
        expect(status.waitingOn).toEqual(['committer']);
    });

    test('no reviewDecision, no skill labels → awaiting_review stage, committer+maintainer expected', () => {
        const status = computeStatus([], null, [], testTeamRoles);

        expect(status.currentStage).toBe('awaiting_review');
        expect(status.expectedReviewers).toEqual(['committer', 'maintainer']);
        expect(status.waitingOn).toEqual(['committer', 'maintainer']);
    });

    test('all expected reviewers have approved → waitingOn is empty even without formal reviewDecision', () => {
        const status = computeStatus(
            [INTERMEDIATE_LABEL],
            'REVIEW_REQUIRED',
            [
                { reviewer: 'alice', state: 'APPROVED', submittedAt: '2026-01-01T00:00:00Z' },
                { reviewer: 'bob', state: 'APPROVED', submittedAt: '2026-01-02T00:00:00Z' },
            ],
            testTeamRoles
        );

        expect(status.waitingOn).toEqual([]);
    });

    test('summary combines currentStage and nextAction', () => {
        // No skill label → expects [committer, maintainer]; bob's approval
        // (maintainer in the fixture roster) satisfies both.
        const status = computeStatus(
            [],
            'APPROVED',
            [{ reviewer: 'bob', state: 'APPROVED', submittedAt: '2026-01-01T00:00:00Z' }],
            testTeamRoles
        );
        expect(status.summary).toContain('approved');
        expect(status.summary).toContain(status.nextAction);
    });

    test('roster unavailable → roster_unavailable stage, regardless of reviewDecision or approvals', () => {
        const status = computeStatus(
            [INTERMEDIATE_LABEL],
            'APPROVED',
            [{ reviewer: 'alice', state: 'APPROVED', submittedAt: '2026-01-01T00:00:00Z' }],
            rosterUnavailable
        );

        expect(status.currentStage).toBe('roster_unavailable');
        expect(status.waitingOn).toEqual(status.expectedReviewers);
    });

    test('regression: an approval followed by a plain comment from the same reviewer still counts as approved', () => {
        // Reproduces the bug where a later COMMENTED review from an
        // already-approving reviewer erased their APPROVED status, since
        // getDetailedReviews only kept the most recent review per reviewer
        // regardless of state. GitHub's own UI keeps the approval standing
        // until the reviewer submits another decisive review.
        const detailedReviews = [
            { reviewer: 'bob', state: 'APPROVED', submittedAt: '2026-01-01T00:00:00Z' },
            { reviewer: 'bob', state: 'COMMENTED', submittedAt: '2026-01-02T00:00:00Z' },
        ];

        const status = computeStatus([INTERMEDIATE_LABEL], 'REVIEW_REQUIRED', detailedReviews, testTeamRoles);

        // bob is the maintainer fixture reviewer, so if the earlier APPROVED
        // had been erased by the later COMMENTED, both gates would still be
        // waiting. With the fix, bob's approval still counts.
        expect(status.waitingOn).toEqual([]);
    });
});

// ---------------------------------------------------------------------------
// formatStatusForLog
// ---------------------------------------------------------------------------

describe('formatStatusForLog', () => {
    test('includes review status, expected reviewers, waiting on, and next action lines', () => {
        const status = computeStatus([ADVANCED_LABEL], 'CHANGES_REQUESTED', [], testTeamRoles);
        const formatted = formatStatusForLog(status);

        expect(formatted).toContain('Review status:');
        expect(formatted).toContain('Expected reviewers:');
        expect(formatted).toContain('Waiting on:');
        expect(formatted).toContain('Next action:');
    });

    test('renders "none" for empty waitingOn', () => {
        // No skill label → expects [committer, maintainer]; bob's approval
        // (maintainer in the fixture roster) satisfies both, so waitingOn
        // is genuinely empty.
        const status = computeStatus(
            [],
            'APPROVED',
            [{ reviewer: 'bob', state: 'APPROVED', submittedAt: '2026-01-01T00:00:00Z' }],
            testTeamRoles
        );
        const formatted = formatStatusForLog(status);
        expect(formatted).toContain('Waiting on: none');
    });
});

// ---------------------------------------------------------------------------
// resolvePrNumber
// ---------------------------------------------------------------------------

describe('resolvePrNumber', () => {
    afterEach(() => {
        delete process.env.PR_NUMBER;
    });

    test('accepts a positive integer from context.payload.pull_request.number', () => {
        const context = { payload: { pull_request: { number: 5 } } };
        expect(resolvePrNumber(context)).toBe(5);
    });

    test('falls back to PR_NUMBER when the payload number is zero or negative', () => {
        process.env.PR_NUMBER = '9';

        expect(resolvePrNumber({ payload: { pull_request: { number: 0 } } })).toBe(9);
        expect(resolvePrNumber({ payload: { pull_request: { number: -3 } } })).toBe(9);
    });

    test('falls back to PR_NUMBER when the payload number is not an integer', () => {
        process.env.PR_NUMBER = '9';

        expect(resolvePrNumber({ payload: { pull_request: { number: 1.5 } } })).toBe(9);
    });

    test('accepts a positive integer PR_NUMBER env var when the payload has none', () => {
        process.env.PR_NUMBER = '12';
        expect(resolvePrNumber({ payload: {} })).toBe(12);
    });

    test('rejects a non-positive or non-numeric PR_NUMBER env var', () => {
        process.env.PR_NUMBER = '-1';
        expect(resolvePrNumber({ payload: {} })).toBeNull();

        process.env.PR_NUMBER = 'not-a-number';
        expect(resolvePrNumber({ payload: {} })).toBeNull();
    });

    test('returns null when neither source has a usable PR number', () => {
        expect(resolvePrNumber({ payload: {} })).toBeNull();
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
        // bob is the maintainer fixture reviewer (see testTeamRoles above),
        // so a single approval from bob clears both the committer and
        // maintainer gates that 'skill: intermediate' expects.
        const github = createMockGithub({
            labels: [INTERMEDIATE_LABEL],
            reviewDecision: 'APPROVED',
            reviews: [{ user: { login: 'bob' }, state: 'APPROVED', submitted_at: '2026-01-01T00:00:00Z' }],
        });
        const context = {
            payload: { pull_request: { number: 42 } },
            repo: { owner: 'o', repo: 'r' },
        };

        const status = await evaluateReviewStatus(github, context);

        expect(status).not.toBeNull();
        expect(status.currentStage).toBe('approved');
    });

    test('does not call GitHub APIs when the payload PR number is invalid', async () => {
        const github = createMockGithub({});
        const listLabelsSpy = jest.spyOn(github.rest.issues, 'listLabelsOnIssue');
        const context = {
            payload: { pull_request: { number: -1 } },
            repo: { owner: 'o', repo: 'r' },
        };

        delete process.env.PR_NUMBER;
        const status = await evaluateReviewStatus(github, context);

        expect(status).toBeNull();
        expect(listLabelsSpy).not.toHaveBeenCalled();
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
