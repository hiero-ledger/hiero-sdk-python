/**
 * PR Draft Explainer Bot
 *
 * Triggers when a pull request is converted to draft.
 *
 * Safety:
 * - Prevents duplicate comments using a unique HTML marker.
 * - Only posts if a CHANGES_REQUESTED review exists.
 * - Fails safely if review lookup fails.
 * - Uses pagination to scan existing comments safely.
 */

const COMMENT_MARKER = "<!-- pr-draft-explainer -->";
const DRY_RUN = process.env.DRY_RUN === "true";
const manualPRNumber = process.env.PR_NUMBER;

/**
 * Checks if the reminder comment already exists.
 * Uses GitHub pagination to safely scan all comments.
 *
 * @param {import("@actions/github").GitHub} params.github - Authenticated GitHub client.
 * @param {string} params.owner - Repository owner.
 * @param {string} params.repo - Repository name.
 * @param {number} params.issueNumber - Pull request number.
 * @param {string} params.marker - Unique marker string to detect duplicate comments.
 * @returns {Promise<boolean>} - True if a comment with the marker exists.
 */

async function commentExists({ github, owner, repo, issueNumber, marker }) {
    console.log("Checking for existing explanation comments...");

    let scanned = 0;
    const MAX_COMMENTS = 500;

    for await (const response of github.paginate.iterator(
        github.rest.issues.listComments,
        {
            owner,
            repo,
            issue_number: issueNumber,
            per_page: 100,
        }
    )) {
        for (const comment of response.data) {
            scanned++;
            if (comment.body?.includes(marker)) {
                console.log(`Found existing explanation comment (scanned ${scanned} comments).`);
                return true;
            }
            if (scanned >= MAX_COMMENTS) {
                console.log(`Reached scan limit (${MAX_COMMENTS} comments) — assuming no duplicate.`);
                return false;
            }
        }
    }

    console.log(`No existing explainer comment found (scanned ${scanned} comments).`);
    return false;
}

/**
 * Builds the draft explainer comment body.
 *
 * @param {string} greetingTarget - Formatted username to greet (e.g., "@username").
 * @returns {string} - Formatted reminder message.
 */

function buildExplainerComment(greetingTarget) {
    return `
${COMMENT_MARKER}
Hi ${greetingTarget}!

We suggested a few updates and moved this PR to **draft** while you apply the feedback. This keeps it out of the review queue until it is ready again.

### What happens next?
- Make the requested changes.
- When you are ready, click **“Ready for review”** (recommended) or use the \`/review\` command.

Thanks again for your contribution!
`.trim();
}

/**
 * Main entry point.
 *
 * Execution Flow:
 * 1. Ensure PR exists in event payload.
 * 2. Prevent duplicate bot comments.
 * 3. Confirm at least one CHANGES_REQUESTED review exists.
 * 4. Post explanation comment.
 */

module.exports = async ({ github, context }) => {
    let pr = context.payload.pull_request;
    let prNumber = pr?.number || manualPRNumber;
    const { owner, repo } = context.repo;

    if (!prNumber) {
        console.log("No PR number found in payload or environment. Exiting.");
        return;
    }
    if (!pr) {
        console.log(`Fetching PR #${prNumber} (manual workflow_dispatch run)...`);

        try {
            const prResponse = await github.rest.pulls.get({
                owner,
                repo,
                pull_number: prNumber,
            });

            pr = prResponse.data;
        } catch (error) {
            console.log(`Failed to fetch PR #${prNumber}: ${error.message}`);
            return;
        }
    }

    const authorLogin = pr.user?.login;
    const greetingTarget = authorLogin ? `@${authorLogin}` : "there";

    if (!pr.draft) {
        console.log(`PR #${prNumber} is not draft. Skipping.`);
        return;
    }

    console.log(`PR #${prNumber} was converted to draft. Checking if explanation is needed.`);

    // Prevent duplicate comments
    let alreadyCommented = false;
    try {
        alreadyCommented = await commentExists({
            github,
            owner,
            repo,
            issueNumber: prNumber,
            marker: COMMENT_MARKER,
        });
    } catch (err) {
        console.log(`Failed to check existing comments on PR #${prNumber} in ${owner}/${repo}: ${err.message}`);
        console.log("Skipping explanation to avoid potential duplicate.");
        return;
    }

    if (alreadyCommented) {
        console.log("Explanation already exists — skipping.");
        return;
    }

    // Only proceed if changes were previously requested on this PR
    try {
        const reviews = await github.rest.pulls.listReviews({
            owner,
            repo,
            pull_number: prNumber,
            per_page: 100,
        });

        // Track the latest review from each reviewer
        const latestReviews = new Map();

        for (const review of reviews.data) {
            const reviewer = review.user?.login;
            if (!reviewer) continue;

            const previous = latestReviews.get(reviewer);

            if (!previous || new Date(review.submitted_at) > new Date(previous.submitted_at)) {
                latestReviews.set(reviewer, review);
            }
        }

        const hasChangeRequest = [...latestReviews.values()].some(
            (review) => review.state === "CHANGES_REQUESTED"
        );

        if (!hasChangeRequest) {
            console.log("No CHANGES_REQUESTED review found. Skipping explanation comment.");
            return;
        }

    } catch (error) {
        console.log(`Review lookup failed for PR #${prNumber}: ${error.message}. Skipping to avoid a false explanation.`);
        return;
    }

    // Post explanation comment
    try {
        if (DRY_RUN) {
            console.log(`[DRY RUN] Explanation comment would be posted on PR #${prNumber}.`);
            return;
        }
        await github.rest.issues.createComment({
            owner,
            repo,
            issue_number: prNumber,
            body: buildExplainerComment(greetingTarget),
        });
        console.log(`Posted draft explanation comment on PR #${prNumber}.`);
    } catch (error) {
        console.log(`Failed to post draft explanation on PR #${prNumber}: ${error.message}`);
    }
};
