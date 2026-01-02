// .github/scripts/gfi_assign_on_comment.js
//
// Assigns human user to Good First Issue when they comment "/assign".
// Posts a comment if the issue is already assigned.
// All other validation and additional GFI comments are handled by other existing bots which can be refactored with time.

const GOOD_FIRST_ISSUE_LABEL = 'Good First Issue';
const UNASSIGNED_GFI_SEARCH_URL =
    'https://github.com/hiero-ledger/hiero-sdk-python/issues?q=is%3Aissue%20state%3Aopen%20label%3A%22Good%20First%20Issue%22%20no%3Aassignee';

/// HELPERS FOR ASSIGNING ///

/**
 * Returns true if /assign appears at the start of a line or comment
 * Optionally preceded or followed by whitespace
 */
function commentRequestsAssignment(body) {
    return typeof body === 'string' &&
        /(^|\n)\s*\/assign(\s|$)/i.test(body);
}

/**
 * Returns true if the issue has the good first issue label.
 */
function issueIsGoodFirstIssue(issue) {
    return issue?.labels?.some(label => label.name === GOOD_FIRST_ISSUE_LABEL);
}

/// HELPERS FOR COMMENTING ///

/**
 * Returns a formatted @username for the current assignee of the issue.
 */
function getCurrentAssigneeMention(issue) {
    const login = issue?.assignees?.[0]?.login;
    return login ? `@${login}` : 'someone';
}

/**
 * Builds a comment explaining that the issue is already assigned.
 * Requester username is passed from main
 */
function commentAlreadyAssigned(requesterUsername, issue) {
    return (
        `Hi @${requesterUsername} — this issue is already assigned to ${getCurrentAssigneeMention(issue)}, so I can’t assign it again.

👉 **Choose a different Good First Issue to work on next:**  
[Browse unassigned Good First Issues](${UNASSIGNED_GFI_SEARCH_URL})

Once you find one you like, comment \`/assign\` to get started.`
    );
}


/// START OF SCRIPT ///
module.exports = async ({ github, context }) => {
    const { issue, comment } = context.payload;
    const { owner, repo } = context.repo;

    // Reject if issue, comment or comment user is missing, reject bots, or if no /assign message
    if (
        !issue?.number ||
        !comment?.body ||
        !comment?.user?.login ||
        comment.user.type === 'Bot' ||
        !commentRequestsAssignment(comment.body)
    ) {
        return;
    }
    // Reject if issue is not a Good First Issue
    if (!issueIsGoodFirstIssue(issue)) return;

    // Get requester username and issue number to enable comments and assignments
    const requesterUsername = comment.user.login;
    const issueNumber = issue.number;

    // Reject if issue is already assigned
    // Comment failure to the requester
    if (issue.assignees?.length > 0) {
        await github.rest.issues.createComment({
            owner,
            repo,
            issue_number: issueNumber,
            body: commentAlreadyAssigned(requesterUsername, issue),
        });
        return;
    }

    // All validations passed and user has requested assignment on a GFI
    // Assign the issue to the requester
    // Do not comment on success
    await github.rest.issues.addAssignees({
        owner,
        repo,
        issue_number: issueNumber,
        assignees: [requesterUsername],
    });
};
