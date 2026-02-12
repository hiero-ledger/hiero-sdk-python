/**
 * PR Draft Ready Reminder Bot
 *
 * Triggers when commits are pushed to a draft PR that has
 * CHANGES_REQUESTED reviews, and posts a reminder comment.
 *
 * Safety:
 * - Runs on pull_request_target (secure pattern)
 * - Skips non-draft PRs
 * - Skips bot-authored PRs
 * - Skips if reviewDecision !== CHANGES_REQUESTED
 * - Prevents duplicate comments via marker
 */

const COMMENT_MARKER = "<!-- draft-ready-reminder-bot -->";

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
    console.log("Checking for existing reminder comments...");

    let scanned = 0;

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
                console.log(`Found existing reminder comment (scanned ${scanned} comments).`);
                return true;
            }
        }
    }

    console.log(`No existing reminder comment found (scanned ${scanned} comments).`);
    return false;
}

/**
 * Builds the draft-ready reminder comment body.
 *
 * @param {string} username - PR author username.
 * @returns {string} - Formatted reminder message.
 */
function buildReminderComment(username) {
    return `
${COMMENT_MARKER}
👋 Hi @${username},

We noticed your pull request has had *recent changes pushed* after *changes were requested*.

If these updates address the feedback, you can:
- resolve any open review conversations (reply if clarification is needed, or mark them as resolved),
- click **“Ready for review”** (recommended), or
- use the \`/review\` command.

Thanks for keeping things moving! 🙌  
— Hiero SDK Automation Team
`.trim();
}

/**
 * Main entry point for the PR Draft Ready Reminder Bot.
 *
 * This function:
 * 1. Resolves the PR number from the event context or environment.
 * 2. Ensures the PR is a draft and not bot-authored.
 * 3. Checks whether the review decision is CHANGES_REQUESTED.
 * 4. Prevents duplicate reminder comments.
 * 5. Posts a reminder comment.
 */

module.exports = async function ({ github, context }) {

    // Resolve PR number from event or workflow_dispatch
    const prNumber =
        context.payload?.pull_request?.number ||
        Number(process.env.PR_NUMBER);

    if (!prNumber) {
        console.log("No PR number found in context or environment — exiting.");
        return;
    }

    const { owner, repo } = context.repo;

    console.log(`Processing PR #${prNumber} in ${owner}/${repo}`);

    // Fetch PR details
    console.log("Fetching PR details...");
    const { data: pr } = await github.rest.pulls.get({
        owner,
        repo,
        pull_number: prNumber,
    });

    console.log(`PR state → draft=${pr.draft}, author=${pr.user.login}, type=${pr.user?.type}`);

    // Early exit: only draft PRs
    if (!pr.draft) {
        console.log("PR is not a draft — skipping reminder.");
        return;
    }

    // Early exit: Bot authored PRs
    if (pr.user?.type === "Bot") {
        console.log("PR authored by bot — skipping reminder.");
        return;
    }

    // Fetch reviewDecision via GraphQL
    console.log("Fetching reviewDecision via GraphQL...");

    const query = `
        query ($owner: String!, $repo: String!, $number: Int!) {
            repository(owner: $owner, name: $repo) {
                pullRequest(number: $number) {
                    reviewDecision
                }
            }
        }
    `;

    let reviewDecision;

    try {
        const result = await github.graphql(query, {
            owner,
            repo,
            number: prNumber,
        });

        reviewDecision = result?.repository?.pullRequest?.reviewDecision;

        if (!reviewDecision) {
            console.log("No reviewDecision returned — skipping.");
            return;
        }

        console.log(`reviewDecision = ${reviewDecision}`);
    } catch (err) {
        console.log("Failed to fetch reviewDecision — skipping reminder.");
        console.log(`Error: ${err.message}`);
        return;
    }

    // Only trigger when changes were requested
    if (reviewDecision !== "CHANGES_REQUESTED") {
        console.log("reviewDecision is not CHANGES_REQUESTED — no reminder needed.");
        return;
    }

    // Prevent duplicate comments
    const alreadyCommented = await commentExists({
        github,
        owner,
        repo,
        issueNumber: prNumber,
        marker: COMMENT_MARKER,
    });

    if (alreadyCommented) {
        console.log("Reminder already exists — skipping.");
        return;
    }

    await github.rest.issues.createComment({
        owner,
        repo,
        issue_number: prNumber,
        body: buildReminderComment(pr.user.login),
    });

    console.log(`Reminder successfully posted on PR #${prNumber}`);
};
