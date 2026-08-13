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
 * role (triage/committer/maintainer). Rather than calling
 * getCollaboratorPermissionLevel per reviewer (see
 * review-sync/helpers/permissions.js), this evaluator cross-checks
 * approvals against docs/team.md (shared/team-roles.js) — the repo's own
 * static, curated roster — to verify which role each approval actually
 * came from. `waitingOn` only drops a role once an approval from someone
 * listed under that role has landed, not just once the raw approval count
 * reaches that position.
 *
 * Roster-failure handling:
 * If docs/team.md can't be read — or reads fine but parses to zero
 * maintainers, which signals heading/format drift since a valid roster
 * always has maintainers — shared/team-roles.js reports `available: false`.
 * computeStatus treats that as its own distinct ROSTER_UNAVAILABLE stage
 * rather than silently falling through to normal gate-checking — an empty
 * roster would otherwise make every approval look unqualified and every
 * role look "still pending", which is indistinguishable from a
 * genuinely-early review state and would misreport PR status.
 */

const {
    AWAITING_REVIEW,
    CHANGES_REQUESTED,
    APPROVED,
    AWAITING_TRIAGE,
    ROSTER_UNAVAILABLE,
    TRIAGE,
    COMMITTER,
    MAINTAINER,
    getExpectedReviewers,
} = require("./shared/review-stages");
const { getTeamRoles } = require("./shared/team-roles");

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
    // bot-pr-draft-explainer.js — with one adjustment: a later COMMENTED
    // review does not supersede an earlier decisive review (APPROVED /
    // CHANGES_REQUESTED) from the same reviewer. GitHub's own UI keeps an
    // approval standing until the reviewer submits another APPROVED or
    // CHANGES_REQUESTED review; a follow-up comment alone isn't a decision
    // and shouldn't overwrite it. A reviewer whose only review is a
    // COMMENTED one is still tracked as COMMENTED.
    const DECISIVE_STATES = new Set(["APPROVED", "CHANGES_REQUESTED", "DISMISSED"]);
    const latestReviews = new Map();

    for (const review of reviews) {
        const reviewer = review.user?.login;
        if (!reviewer) continue;

        const previous = latestReviews.get(reviewer);

        if (!previous) {
            latestReviews.set(reviewer, review);
            continue;
        }

        const isNewer = new Date(review.submitted_at) > new Date(previous.submitted_at);
        if (!isNewer) continue;

        const wouldOverwriteDecisiveWithComment =
            review.state === "COMMENTED" && DECISIVE_STATES.has(previous.state);
        if (wouldOverwriteDecisiveWithComment) continue;

        latestReviews.set(reviewer, review);
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
 * @param {{available: boolean, triage: Set<string>, committer: Set<string>, maintainer: Set<string>}} teamRoles
 *   - Roster data, as returned by shared/team-roles.js's getTeamRoles(). Passed
 *   in rather than fetched here so callers control the read (live
 *   docs/team.md in production, fixture data in tests).
 * @returns {{
 *   currentStage: string,
 *   expectedReviewers: string[],
 *   waitingOn: string[],
 *   nextAction: string,
 *   summary: string,
 * }}
 */
function computeStatus(labels, reviewDecision, detailedReviews, teamRoles) {
    const expectedReviewers = getExpectedReviewers(labels);
    const { available, triage, committer, maintainer } = teamRoles;

    // If the roster couldn't be read, stop here — don't let empty role
    // sets masquerade as "no approvals yet". Report the failure explicitly
    // instead of computing a normal (and misleading) gate status.
    if (!available) {
        const summary = `${ROSTER_UNAVAILABLE} — Could not read docs/team.md, so reviewer roles can't be verified. Fix the file/path and re-run.`;

        return {
            currentStage: ROSTER_UNAVAILABLE,
            expectedReviewers,
            waitingOn: expectedReviewers,
            nextAction: "Could not read docs/team.md — reviewer roles unavailable. Fix the file/path and re-run.",
            summary,
        };
    }

    // Role hierarchy: a maintainer's approval also satisfies committer/
    // triage gates, and a committer's approval also satisfies triage gates,
    // since those roles are supersets of authority.
    const qualifiedFor = {
        [TRIAGE]: new Set([...triage, ...committer, ...maintainer]),
        [COMMITTER]: new Set([...committer, ...maintainer]),
        [MAINTAINER]: maintainer,
    };

    const approvedReviews = detailedReviews.filter((r) => r.state === "APPROVED");

    const hasQualifiedApproval = (role) =>
        approvedReviews.some((r) => qualifiedFor[role]?.has((r.reviewer || "").toLowerCase()));

    // Each expected role is only cleared once an approval from someone
    // actually holding that role (or a higher one) has landed — not just
    // once the raw approval count reaches that position, and not just
    // because GitHub's reviewDecision says "APPROVED" (branch protection
    // may only require *any* single approval, which can be satisfied by a
    // triage-only approval on a PR that also expects a committer/maintainer
    // sign-off).
    const outstandingRoles = expectedReviewers.filter((role) => !hasQualifiedApproval(role));

    let currentStage;
    let waitingOn;
    let nextAction;

    // NOTE: reviewDecision here is GitHub's literal GraphQL enum value
    // ("APPROVED", "CHANGES_REQUESTED", "REVIEW_REQUIRED", or null) — these
    // are matched against string literals, not our internal stage constants
    // from shared/review-stages.js, which use a different casing/format and
    // are only used for the *output* currentStage value.
    if (reviewDecision === "CHANGES_REQUESTED") {
        currentStage = CHANGES_REQUESTED;
        // A fresh review cycle is needed from everyone expected once changes
        // are pushed, so treat the full expected list as outstanding.
        waitingOn = expectedReviewers;
        nextAction = `Address requested changes, then re-request review from: ${waitingOn.join(", ") || "none"}.`;
    } else if (reviewDecision === "APPROVED" && outstandingRoles.length === 0) {
        currentStage = APPROVED;
        waitingOn = [];
        nextAction = "Ready to merge.";
    } else {
        // null, REVIEW_REQUIRED, or a GitHub-level "APPROVED" that hasn't
        // actually satisfied every role-qualified gate this evaluator
        // expects yet.
        waitingOn = outstandingRoles;

        currentStage =
            expectedReviewers[0] === TRIAGE && waitingOn.includes(TRIAGE)
                ? AWAITING_TRIAGE
                : AWAITING_REVIEW;

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
function resolvePrNumber(context) {
    const fromPayload = context.payload?.pull_request?.number;
    if (Number.isInteger(fromPayload) && fromPayload > 0) {
        return fromPayload;
    }

    const fromEnv = Number(process.env.PR_NUMBER);
    if (Number.isInteger(fromEnv) && fromEnv > 0) {
        return fromEnv;
    }

    return null;
}

async function evaluateReviewStatus(github, context) {
    const prNumber = resolvePrNumber(context);

    if (!prNumber) {
        console.log("No valid PR number found in context or environment — exiting.");
        return null;
    }

    const { owner, repo } = context.repo;

    console.log(`Evaluating review status for PR #${prNumber} in ${owner}/${repo}`);

    const [labels, reviewDecision, detailedReviews] = await Promise.all([
        getPRLabels(github, owner, repo, prNumber),
        getReviewState(github, owner, repo, prNumber),
        getDetailedReviews(github, owner, repo, prNumber),
    ]);

    const status = computeStatus(labels, reviewDecision, detailedReviews, getTeamRoles());

    console.log(formatStatusForLog(status));

    return status;
}

module.exports = {
    getPRLabels,
    getReviewState,
    getDetailedReviews,
    computeStatus,
    formatStatusForLog,
    resolvePrNumber,
    evaluateReviewStatus,
};
