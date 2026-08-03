/**
 * PR Review Status Evaluator
 *
 * Computes a structured "review status" for a pull request: what stage of
 * review it's in, who is expected to review it, who it's still waiting on,
 * and what the next action should be.
 *
 * This module is read-only — it never posts comments or mutates PR state.
 * It's designed to be imported by a GitHub Actions workflow via
 * actions/github-script and its output logged / exposed as job outputs.
 *
 * Data sources:
 * - PR labels: REST (github.rest.issues.listLabelsOnIssue), paginated,
 *   following the pagination pattern from bot-pr-draft-ready-reminder.js.
 * - reviewDecision: GraphQL, following the pattern from
 *   bot-pr-draft-ready-reminder.js.
 * - Per-reviewer review states: REST (github.rest.pulls.listReviews),
 *   deduplicated to each reviewer's latest review, following the pattern
 *   from bot-pr-draft-explainer.js.
 *
 * Reviewer-role assumption:
 * GitHub's REST/GraphQL APIs return reviews by username, not by CODEOWNERS
 * role (triage/committer/maintainer) — resolving a username's role would
 * require extra org/team-membership calls. To keep this evaluator simple
 * and avoid that extra API surface, `expectedReviewers` (from
 * shared/review-stages.js) is treated as an ordered list of sequential
 * approval gates: the first entry must approve before we consider the
 * second one "in progress". `waitingOn` is derived by counting how many
 * approving reviews have landed and slicing the remaining expected
 * reviewer types off that list. This is an approximation, not a true
 * role-aware waiting-on computation.
 */

const {
    AWAITING_REVIEW,
    CHANGES_REQUESTED,
    APPROVED,
    AWAITING_TRIAGE,
    TRIAGE,
    getExpectedReviewers,
} = require("./shared/review-stages");

const DRY_RUN = process.env.DRY_RUN === "true";

/**
 * Fetches the labels currently applied to a PR via the REST API.
 *
 * @param {import("@actions/github").GitHub} github - Authenticated GitHub client.
 * @param {string} owner - Repository owner.
 * @param {string} repo - Repository name.
 * @param {number} prNumber - Pull request number.
 * @returns {Promise<string[]>} - Array of label names.
 */
async function getPRLabels(github, owner, repo, prNumber) {
    const labels = [];

    try {
        for await (const response of github.paginate.iterator(
            github.rest.issues.listLabelsOnIssue,
            {
                owner,
                repo,
                issue_number: prNumber,
                per_page: 100,
            }
        )) {
            for (const label of response.data) {
                if (label?.name) {
                    labels.push(label.name);
                }
            }
        }
    } catch (err) {
        console.log(`Failed to fetch labels for PR #${prNumber} in ${owner}/${repo}: ${err.message}`);
        return [];
    }

    return labels;
}

/**
 * Fetches the PR's overall reviewDecision via GraphQL.
 *
 * @param {import("@actions/github").GitHub} github - Authenticated GitHub client.
 * @param {string} owner - Repository owner.
 * @param {string} repo - Repository name.
 * @param {number} prNumber - Pull request number.
 * @returns {Promise<string|null>} - reviewDecision (e.g. "APPROVED",
 *   "CHANGES_REQUESTED", "REVIEW_REQUIRED") or null if unavailable.
 */
async function getReviewState(github, owner, repo, prNumber) {
    const query = `
        query ($owner: String!, $repo: String!, $number: Int!) {
            repository(owner: $owner, name: $repo) {
                pullRequest(number: $number) {
                    reviewDecision
                }
            }
        }
    `;

    try {
        const result = await github.graphql(query, {
            owner,
            repo,
            number: prNumber,
        });

        return result?.repository?.pullRequest?.reviewDecision ?? null;
    } catch (err) {
        console.log(`Failed to fetch reviewDecision for PR #${prNumber} in ${owner}/${repo}: ${err.message}`);
        return null;
    }
}

/**
 * Fetches each reviewer's latest review state via the paginated REST API.
 *
 * @param {import("@actions/github").GitHub} github - Authenticated GitHub client.
 * @param {string} owner - Repository owner.
 * @param {string} repo - Repository name.
 * @param {number} prNumber - Pull request number.
 * @returns {Promise<Array<{reviewer: string, state: string, submittedAt: string}>>}
 */
async function getDetailedReviews(github, owner, repo, prNumber) {
    let reviews = [];

    try {
        for await (const response of github.paginate.iterator(
            github.rest.pulls.listReviews,
            {
                owner,
                repo,
                pull_number: prNumber,
                per_page: 100,
            }
        )) {
            reviews.push(...response.data);
        }
    } catch (err) {
        console.log(`Failed to fetch reviews for PR #${prNumber} in ${owner}/${repo}: ${err.message}`);
        return [];
    }

    // Track the latest review from each reviewer, same pattern as
    // bot-pr-draft-explainer.js.
    const latestReviews = new Map();

    for (const review of reviews) {
        const reviewer = review.user?.login;
        if (!reviewer) continue;

        const previous = latestReviews.get(reviewer);

        if (!previous || new Date(review.submitted_at) > new Date(previous.submitted_at)) {
            latestReviews.set(reviewer, review);
        }
    }

    return [...latestReviews.entries()].map(([reviewer, review]) => ({
        reviewer,
        state: review.state,
        submittedAt: review.submitted_at,
    }));
}

/**
 * Computes the structured review status for a PR from already-fetched data.
 *
 * @param {string[]} labels - PR label names.
 * @param {string|null} reviewDecision - GraphQL reviewDecision value.
 * @param {Array<{reviewer: string, state: string, submittedAt: string}>} detailedReviews
 * @returns {{
 *   currentStage: string,
 *   expectedReviewers: string[],
 *   waitingOn: string[],
 *   nextAction: string,
 *   summary: string,
 * }}
 */
function computeStatus(labels, reviewDecision, detailedReviews) {
    const expectedReviewers = getExpectedReviewers(labels);

    const approvedCount = detailedReviews.filter((r) => r.state === "APPROVED").length;

    let currentStage;
    let waitingOn;
    let nextAction;

    // NOTE: reviewDecision here is GitHub's literal GraphQL enum value
    // ("APPROVED", "CHANGES_REQUESTED", "REVIEW_REQUIRED", or null) — these
    // are matched against string literals, not our internal stage constants
    // from shared/review-stages.js, which use a different casing/format and
    // are only used for the *output* currentStage value.
    if (reviewDecision === "APPROVED") {
        currentStage = APPROVED;
        waitingOn = [];
        nextAction = "Ready to merge.";
    } else if (reviewDecision === "CHANGES_REQUESTED") {
        currentStage = CHANGES_REQUESTED;
        // A fresh review cycle is needed from everyone expected once changes
        // are pushed, so treat the full expected list as outstanding.
        waitingOn = expectedReviewers;
        nextAction = `Address requested changes, then re-request review from: ${waitingOn.join(", ") || "none"}.`;
    } else {
        // null or REVIEW_REQUIRED — no decision reached yet.
        waitingOn = expectedReviewers.slice(approvedCount);

        currentStage =
            expectedReviewers[0] === TRIAGE && approvedCount === 0 ? AWAITING_TRIAGE : AWAITING_REVIEW;

        nextAction =
            waitingOn.length > 0
                ? `Waiting on review from: ${waitingOn.join(", ")}.`
                : "Waiting on review decision.";
    }

    const summary = `${currentStage} — ${nextAction}`;

    return {
        currentStage,
        expectedReviewers,
        waitingOn,
        nextAction,
        summary,
    };
}

/**
 * Formats a computed status object as clear multi-line log output.
 *
 * @param {ReturnType<typeof computeStatus>} status
 * @returns {string}
 */
function formatStatusForLog(status) {
    const lines = [
        `Review status: ${status.currentStage}`,
        `Expected reviewers: ${status.expectedReviewers.join(", ") || "none"}`,
        `Waiting on: ${status.waitingOn.join(", ") || "none"}`,
        `Next action: ${status.nextAction}`,
    ];

    return lines.join("\n");
}

/**
 * Orchestrates the full evaluation: resolves the PR number from context,
 * fetches labels / reviewDecision / detailed reviews, and computes status.
 *
 * @param {import("@actions/github").GitHub} github - Authenticated GitHub client.
 * @param {import("@actions/github").Context} context - Workflow run context.
 * @returns {Promise<ReturnType<typeof computeStatus>|null>} - null if no PR
 *   number could be resolved.
 */
async function evaluateReviewStatus(github, context) {
    const prNumber =
        context.payload?.pull_request?.number || Number(process.env.PR_NUMBER);

    if (!prNumber) {
        console.log("No PR number found in context or environment — exiting.");
        return null;
    }

    const { owner, repo } = context.repo;

    if (DRY_RUN) {
        console.log(`[DRY RUN] Evaluating review status for PR #${prNumber} in ${owner}/${repo}`);
    } else {
        console.log(`Evaluating review status for PR #${prNumber} in ${owner}/${repo}`);
    }

    const [labels, reviewDecision, detailedReviews] = await Promise.all([
        getPRLabels(github, owner, repo, prNumber),
        getReviewState(github, owner, repo, prNumber),
        getDetailedReviews(github, owner, repo, prNumber),
    ]);

    const status = computeStatus(labels, reviewDecision, detailedReviews);

    console.log(formatStatusForLog(status));

    return status;
}

module.exports = {
    getPRLabels,
    getReviewState,
    getDetailedReviews,
    computeStatus,
    formatStatusForLog,
    evaluateReviewStatus,
};
