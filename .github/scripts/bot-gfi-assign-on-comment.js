// .github/scripts/bot-gfi_assign_on_comment.js
//
// Assigns human user to Good First Issue when they comment "/assign".
// Posts a comment if the issue is already assigned.
// All other validation and additional GFI comments are handled by other existing bots which can be refactored with time.

const fs = require('fs'); // For spam list

const GOOD_FIRST_ISSUE_LABEL = 'Good First Issue';
const UNASSIGNED_GFI_SEARCH_URL =
    'https://github.com/hiero-ledger/hiero-sdk-python/issues?q=is%3Aissue%20state%3Aopen%20label%3A%22Good%20First%20Issue%22%20no%3Aassignee';

const SPAM_LIST_PATH = '.github/spam-list.txt';

/// --------------------
/// NEW HELPERS (LIMIT ENFORCEMENT)
/// --------------------

function isSpamUser(username) {
    if (!fs.existsSync(SPAM_LIST_PATH)) return false;

    const list = fs.readFileSync(SPAM_LIST_PATH, 'utf8')
        .split('\n')
        .map(l => l.trim())
        .filter(l => l && !l.startsWith('#'));

    return list.includes(username);
}

async function getOpenAssignments({ github, owner, repo, username }) {
    const issues = await github.paginate(
        github.rest.issues.listForRepo,
        {
            owner,
            repo,
            assignee: username,
            state: 'open',
            per_page: 100,
        }
    );
    return issues.length;
}

/// HELPERS FOR ASSIGNING ///

/**
 * Returns true if /assign appears as a standalone command in the comment
 */
function commentRequestsAssignment(body) {
    const matches =
        typeof body === 'string' &&
        /(^|\s)\/assign(\s|$)/i.test(body);

    console.log('[gfi-assign] commentRequestsAssignment:', {
        body,
        matches,
    });

    return matches;
}

/**
 * Returns true if the issue has the good first issue label.
 */
function issueIsGoodFirstIssue(issue) {
    const labels = issue?.labels?.map(label => label.name) ?? [];
    const isGfi = labels.some(label =>
        typeof label === 'string' && label.toLowerCase() === GOOD_FIRST_ISSUE_LABEL.toLowerCase()
    );

    console.log('[gfi-assign] issueIsGoodFirstIssue:', {
        labels,
        expected: GOOD_FIRST_ISSUE_LABEL,
        isGfi,
    });

    return isGfi;
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

// HELPERS FOR PEOPLE THAT WANT TO BE ASSIGNED BUT DID NOT READ INSTRUCTIONS
const ASSIGN_REMINDER_MARKER = '<!-- GFI assign reminder -->';

function buildAssignReminder(username) {
    return `${ASSIGN_REMINDER_MARKER}
👋 Hi @${username}!

If you’d like to work on this **Good First Issue**, just comment:

\`\`\`
/assign
\`\`\`

and you’ll be automatically assigned. Feel free to ask questions here if anything is unclear!`;
}

/// HELPERS TO DETECT COLLABORATORS ///

function hasValidInputs({ github, owner, repo, username }) {
    return Boolean(
        github &&
        typeof owner === 'string' &&
        typeof repo === 'string' &&
        typeof username === 'string' &&
        owner &&
        repo &&
        username
    );
}

function isPermissionFailure(error) {
    return error?.status === 401 || error?.status === 403;
}

async function isRepoCollaborator({ github, owner, repo, username }) {
    if (!hasValidInputs({ github, owner, repo, username })) {
        console.log('[gfi-assign] isRepoCollaborator: invalid args', {
            owner,
            repo,
            username,
        });
        return false;
    }

    try {
        const response = await github.rest.repos.getCollaboratorPermissionLevel({
            owner,
            repo,
            username,
        });

        const permission = response?.data?.permission;

        const isTeamMember =
            permission === 'admin' ||
            permission === 'write' ||
            permission === 'maintain' ||
            permission === 'read';

        console.log('[gfi-assign] isRepoCollaborator:', {
            username,
            permission,
            isTeamMember,
        });

        return isTeamMember;
    } catch (error) {
        if (isPermissionFailure(error) || error?.status === 404) {
            console.log(
                '[gfi-assign] isRepoCollaborator: no permission / not collaborator',
                { username, status: error.status }
            );
            return false;
        }
        throw error;
    }
}



/// START OF SCRIPT ///
module.exports = async ({ github, context }) => {
    try {
        const { issue, comment } = context.payload;
        const { owner, repo } = context.repo;

        console.log('[gfi-assign] Payload snapshot:', {
            issueNumber: issue?.number,
            commenter: comment?.user?.login,
            commenterType: comment?.user?.type,
            commentBody: comment?.body,
        });

        // Reject if issue, comment or comment user is missing, reject bots, or if no /assign message
        if (!issue?.number) {
            console.log('[gfi-assign] Exit: missing issue number');
            return;
        }

        if (!comment?.body) {
            console.log('[gfi-assign] Exit: missing comment body');
            return;
        }

        if (!comment?.user?.login) {
            console.log('[gfi-assign] Exit: missing comment user login');
            return;
        }

        if (comment.user.type === 'Bot') {
            console.log('[gfi-assign] Exit: comment authored by bot');
            return;
        }

        if (!commentRequestsAssignment(comment.body)) {
            // Only remind if:
            // - GFI
            // - unassigned
            // - reminder not already posted
            if (
                issueIsGoodFirstIssue(issue) &&
                !issue.assignees?.length
            ) {
                const username = comment.user.login;

                const isTeamMember = await isRepoCollaborator({
                    github,
                    owner,
                    repo,
                    username,
                });

                if (isTeamMember) {          
                    console.log('[gfi-assign] Skip reminder: commenter is collaborator');
                    return;
                }

                const comments = await github.paginate(
                    github.rest.issues.listComments,
                    {
                        owner,
                        repo,
                        issue_number: issue.number,
                        per_page: 100,
                    }
                );

                const reminderAlreadyPosted = comments.some(c =>
                    c.body?.includes(ASSIGN_REMINDER_MARKER)
                );

                if (!reminderAlreadyPosted) {
                    await github.rest.issues.createComment({
                        owner,
                        repo,
                        issue_number: issue.number,
                        body: buildAssignReminder(comment.user.login),
                    });

                    console.log('[gfi-assign] Posted /assign reminder');
                }
            }

            console.log('[gfi-assign] Exit: comment does not request assignment');
            return;
        }

        console.log('[gfi-assign] Assignment command detected');

        // Reject if issue is not a Good First Issue
        if (!issueIsGoodFirstIssue(issue)) {
            console.log('[gfi-assign] Exit: issue is not a Good First Issue');
            return;
        }

        console.log('[gfi-assign] Issue is labeled Good First Issue');

        // Get requester username and issue number to enable comments and assignments
        const requesterUsername = comment.user.login;
        const issueNumber = issue.number;

        console.log('[gfi-assign] Requester:', requesterUsername);
        console.log('[gfi-assign] Current assignees:', issue.assignees?.map(a => a.login));

        // Reject if issue is already assigned
        // Comment failure to the requester
        if (issue.assignees?.length > 0) {
            console.log('[gfi-assign] Exit: issue already assigned');

            await github.rest.issues.createComment({
                owner,
                repo,
                issue_number: issueNumber,
                body: commentAlreadyAssigned(requesterUsername, issue),
            });

            console.log('[gfi-assign] Posted already-assigned comment');
            return;
        }

        // -------------------------------
        // ENFORCE ASSIGNMENT LIMITS
        // -------------------------------

        const openCount = await getOpenAssignments({
            github,
            owner,
            repo,
            username: requesterUsername,
        });

        const spamUser = isSpamUser(requesterUsername);
        const maxAllowed = spamUser ? 1 : 2;

        console.log('[gfi-assign] Limit check:', {
            requesterUsername,
            openCount,
            spamUser,
            maxAllowed,
        });

        if (openCount >= maxAllowed) {
            const message = spamUser
                ? `Hi @${requesterUsername}, you are limited to **1 active issue** at a time. Please complete your current assignment before requesting another.`
                : `Hi @${requesterUsername}, you already have **2 open assignments**. Please finish one before requesting another.`;

            await github.rest.issues.createComment({
                owner,
                repo,
                issue_number: issueNumber,
                body: message,
            });

            console.log('[gfi-assign] Assignment blocked due to limit');
            return;
        }

        console.log('[gfi-assign] Assigning issue to requester');

        // All validations passed and user has requested assignment on a GFI
        // Assign the issue to the requester
        // Do not comment on success
        await github.rest.issues.addAssignees({
            owner,
            repo,
            issue_number: issueNumber,
            assignees: [requesterUsername],
        });

        console.log('[gfi-assign] Assignment completed successfully');

        // Chain mentor assignment after successful GFI assignment
        let mentorAssignmentSucceeded = false;
        try {
            const assignMentor = require('./bot-mentor-assignment.js');
            await assignMentor({
                github,
                context,
                assignee: { login: requesterUsername, type: 'User' }  // Pass freshly-assigned username
            });
            mentorAssignmentSucceeded = true;
            console.log('[gfi-assign] Mentor assignment chained successfully');
        } catch (error) {
            console.error('[gfi-assign] Mentor assignment failed but user assignment succeeded:', {
                message: error.message,
                status: error.status,
                owner,
                repo,
                issueNumber,
                assignee: requesterUsername,
            });
            // Don't throw error - user assignment was successful
        }

        // Chain CodeRabbit plan trigger after mentor assignment
        // Only trigger if mentor assignment succeeded to maintain the expected flow
        if (mentorAssignmentSucceeded) {
            try {
                const { triggerCodeRabbitPlan, hasExistingCodeRabbitPlan } = require('./coderabbit_plan_trigger.js');
                
                // Check if CodeRabbit plan already exists to avoid duplicate comments
                const planExists = await hasExistingCodeRabbitPlan(github, owner, repo, issueNumber);
                if (planExists) {
                    console.log('[gfi-assign] CodeRabbit plan already exists, skipping');
                } else {
                    await triggerCodeRabbitPlan(github, owner, repo, issue);
                    console.log('[gfi-assign] CodeRabbit plan chained successfully');
                }
            } catch (error) {
                console.error('[gfi-assign] CodeRabbit plan failed but user assignment succeeded:', {
                    message: error.message,
                    status: error.status,
                    owner,
                    repo,
                    issueNumber,
                    assignee: requesterUsername,
                });
                // Don't throw error - user assignment was successful
            }
        }
    } catch (error) {
        console.error('[gfi-assign] Error:', {
            message: error.message,
            status: error.status,
            issueNumber: context.payload.issue?.number,
            commenter: context.payload.comment?.user?.login,
        });
        throw error;
    }
};
