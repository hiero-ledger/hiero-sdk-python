// .github/scripts/bot-beginner-assign-on-comment.js
//
// Assigns human user to "beginner" issue when they comment "/assign".
// Posts a comment if the issue is already assigned.
// Skips reminders if the commenter is a team member (write access or higher).

const TARGET_LABEL = 'beginner';
const UNASSIGNED_SEARCH_URL =
    'https://github.com/hiero-ledger/hiero-sdk-python/issues?q=is%3Aissue%20state%3Aopen%20label%3Abeginner%20no%3Aassignee';

/// HELPERS FOR ASSIGNING ///

/**
 * Returns true if /assign appears as a standalone command in the comment
 */
function commentRequestsAssignment(body) {
    const matches =
        typeof body === 'string' &&
        /(^|\s)\/assign(\s|$)/i.test(body);

    return matches;
}

/**
 * Returns true if the issue has the beginner label.
 */
function issueIsBeginnerIssue(issue) {
    const labels = issue?.labels?.map(label => label.name) ?? [];
    return labels.some(label => 
        typeof label === 'string' && label.toLowerCase() === TARGET_LABEL.toLowerCase()
    );
}

/**
 * Checks if a user has write/maintain/admin access to the repo.
 */
async function isTeamMember(github, owner, repo, username) {
    try {
        const { data } = await github.rest.repos.getCollaboratorPermissionLevel({
            owner,
            repo,
            username,
        });
        // 'admin', 'maintain', 'write' imply team member status
        return ['admin', 'maintain', 'write'].includes(data.permission);
    } catch (error) {
        console.error(`[beginner-assign] Error checking permissions for ${username}:`, error.message);
        return false; // Fail safe: treat as non-member if check fails
    }
}

/// HELPERS FOR COMMENTING ///

function getCurrentAssigneeMention(issue) {
    const login = issue?.assignees?.[0]?.login;
    return login ? `@${login}` : 'someone';
}

function commentAlreadyAssigned(requesterUsername, issue) {
    return (
        `Hi @${requesterUsername} — this issue is already assigned to ${getCurrentAssigneeMention(issue)}, so I can’t assign it again.

👉 **Choose a different beginner issue to work on next:** [Browse unassigned beginner issues](${UNASSIGNED_SEARCH_URL})

Once you find one you like, comment \`/assign\` to get started.`
    );
}

// Unique marker to ensure we don't clash with GFI reminders
const ASSIGN_REMINDER_MARKER = '';

function buildAssignReminder(username) {
    return `${ASSIGN_REMINDER_MARKER}
👋 Hi @${username}!

If you’d like to work on this **beginner issue**, just comment:

\`\`\`
/assign
\`\`\`

and you’ll be automatically assigned. Feel free to ask questions here if anything is unclear!`;
}

/// START OF SCRIPT ///
module.exports = async ({ github, context }) => {
    try {
        const { issue, comment } = context.payload;
        const { owner, repo } = context.repo;

        // Validations
        if (!issue?.number || !comment?.body || !comment?.user?.login) return;
        if (comment.user.type === 'Bot') return;

        // 1. Handle Non-Assignment Comments (Potential Reminders)
        if (!commentRequestsAssignment(comment.body)) {
            // Only remind if:
            // - It is a beginner issue
            // - It is unassigned
            if (issueIsBeginnerIssue(issue) && !issue.assignees?.length) {
                
                // NEW: Check if the commenter is a team member
                // We do not want to nag maintainers with "type /assign" instructions
                const isMember = await isTeamMember(github, owner, repo, comment.user.login);
                if (isMember) {
                    console.log(`[beginner-assign] User ${comment.user.login} is a team member. Skipping reminder.`);
                    return;
                }

                // Check duplicates
                const comments = await github.paginate(
                    github.rest.issues.listComments,
                    { owner, repo, issue_number: issue.number, per_page: 100 }
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
                    console.log('[beginner-assign] Posted /assign reminder');
                }
            }
            return;
        }

        // 2. Handle /assign Command
        if (!issueIsBeginnerIssue(issue)) {
            console.log('[beginner-assign] Exit: issue not labeled beginner');
            return;
        }

        const requesterUsername = comment.user.login;

        // Check if already assigned
        if (issue.assignees?.length > 0) {
            await github.rest.issues.createComment({
                owner,
                repo,
                issue_number: issue.number,
                body: commentAlreadyAssigned(requesterUsername, issue),
            });
            return;
        }

        // Assign
        await github.rest.issues.addAssignees({
            owner,
            repo,
            issue_number: issue.number,
            assignees: [requesterUsername],
        });

        console.log(`[beginner-assign] Assigned issue #${issue.number} to ${requesterUsername}`);

    } catch (error) {
        console.error('[beginner-assign] Error:', error.message);
        throw error;
    }
};