/*
==============================================================================
Executes When:
  - Triggered by GitHub Actions workflow on event: 'issue_comment' (created).
  - Target: Issues specifically labeled with "beginner".

Goal:
  It acts as an automated onboarding assistant for "beginner" issues. It allows
  contributors to self-assign using a command and nudges new contributors who
  express interest but forget to assign themselves, while preventing spam.

------------------------------------------------------------------------------
Flow: Basic Idea
  1. Listens for comments on issues.
  2. Ignores Pull Requests and issues missing the "beginner" label.
  3. Detects if the user typed "/assign".
     - If YES: Assigns the user to the issue (if currently unassigned).
     - If NO: Checks if the user is an external contributor expressing interest.
       If so, it replies with instructions on how to use the assign command.

------------------------------------------------------------------------------
Flow: Detailed Technical Steps

1️⃣ Validation & filtering
    - Checks payload to ensure it is an Issue Comment (not a PR).
    - Checks if the issue has the specific label "beginner". If not, exits.

2️⃣ Permission Analysis (Team vs. Contributor)
    - Action: Queries 'github.rest.repos.getCollaboratorPermissionLevel'.
    - Logic:
      * 'admin', 'maintain', 'write' -> Treated as Team Member (Bot ignores them).
      * 'read', 'none'               -> Treated as External Contributor (Bot helps them).

3️⃣ Logic Branch A: The "/assign" Command
    - Trigger: User comment matches regex /(^|\s)\/assign(\s|$)/i.
    - Check: Is the issue already assigned?
      * Yes -> Log and exit (prevent overwriting assignees).
      * No  -> API Call: Add commenter to 'assignees'.

4️⃣ Logic Branch B: The Helper Reminder
    - Trigger: Generic comment (e.g., "I want to work on this").
    - Condition 1: Issue must be unassigned.
    - Condition 2: Commenter must NOT be a Team Member (avoids nagging maintainers).
    - Condition 3: Duplicate Check.
      * Scans previous comments for a hidden marker: "<!-- GFI assign reminder -->".
      * If found -> Exits to avoid spamming the thread.
    - Action: Posts a comment with the hidden marker and instructions.

------------------------------------------------------------------------------
Parameters:
  - { github, context }: Standard objects provided by 'actions/github-script'.

Environment Variables / Context:
  - payload.issue: The issue object triggering the workflow.
  - payload.comment: The comment object containing the user's text.

Dependencies:
  - GitHub REST API (via 'github' octokit client).

Permissions Required (in Workflow YAML):
  - 'issues: write' (to post comments and assign users).
  - 'pull-requests: none' (logic explicitly excludes PRs).

Returns:
  - void. (Logs actions to console for debugging).
==============================================================================
*/

module.exports = async ({ github, context }) => {
  const { payload } = context;
  const issue = payload.issue;
  const comment = payload.comment;
  const repo = payload.repository;

  // 1. Basic Validation
  if (!issue || !comment || !repo || issue.pull_request) {
    console.log("[Beginner Bot] Invalid payload or PR comment. Exiting.");
    return;
  }

  // 2. Label Check
  const hasBeginnerLabel = issue.labels.some((label) => label.name === "beginner");
  if (!hasBeginnerLabel) {
    console.log(`[Beginner Bot] Issue #${issue.number} does not have 'beginner' label. Exiting.`);
    return;
  }

  // 3. Permission Check Helper
  async function hasTeamMemberAccess(username) {
    try {
      const { data: permissions } =
        await github.rest.repos.getCollaboratorPermissionLevel({
          owner: repo.owner.login,
          repo: repo.name,
          username: username,
        });
      
      // 'admin', 'maintain', 'write' are considered team members
      // 'triage', 'read', 'none' are considered external contributors
      const isTeam = ["admin", "maintain", "write"].includes(permissions.permission);
      console.log(`[Beginner Bot] User '${username}' has permission: '${permissions.permission}'. Team member? ${isTeam}`);
      return isTeam;
    } catch (error) {
      console.log(`[Beginner Bot] Error checking permissions for ${username}: ${error.message}`);
      return false;
    }
  }

  const commenter = comment.user.login;
  const commentBody = comment.body.toLowerCase();
  const isAssignCommand = /(^|\s)\/assign(\s|$)/i.test(commentBody);

  // 4. Logic Branch
  if (isAssignCommand) {
    // --- ASSIGNMENT LOGIC ---
    if (issue.assignees && issue.assignees.length > 0) {
        console.log(`[Beginner Bot] Issue #${issue.number} is already assigned. Ignoring /assign command.`);
        return;
    }

    console.log(`[Beginner Bot] Assigning issue #${issue.number} to @${commenter}...`);
    await github.rest.issues.addAssignees({
        owner: repo.owner.login,
        repo: repo.name,
        issue_number: issue.number,
        assignees: [commenter],
      });
      console.log(`[Beginner Bot] Successfully assigned.`);

  } else {
    // --- REMINDER LOGIC ---
    
    // Check 1: Is issue already assigned?
    if (issue.assignees && issue.assignees.length > 0) {
        console.log(`[Beginner Bot] Issue #${issue.number} is already assigned. Skipping reminder.`);
        return; 
    }

    // Check 2: Is user a team member?
    if (await hasTeamMemberAccess(commenter)) {
      console.log(`[Beginner Bot] Commenter @${commenter} is a team member. Skipping reminder to avoid spam.`);
      return;
    }

    // Check 3: Duplicate Reminder?
    // CHANGE THIS LINE: Use a unique comment string
    const REMINDER_MARKER = "<!-- GFI assign reminder -->"; 
    
    const { data: comments } = await github.rest.issues.listComments({
        owner: repo.owner.login,
        repo: repo.name,
        issue_number: issue.number,
    });
    
    // This will now only return true if a comment actually contains the specific marker
    if (comments.some((c) => c.body.includes(REMINDER_MARKER))) {
        console.log("[Beginner Bot] Reminder already exists on this issue. Skipping.");
        return;
    }

    // POST REMINDER
    console.log(`[Beginner Bot] Posting help reminder for @${commenter}...`);
    
    // The marker is added to the start of the body, invisible to the user
    const reminderBody = `${REMINDER_MARKER}\n👋 Hi @${commenter}! If you'd like to work on this issue, please comment \`/assign\` to get assigned.`;
    
    await github.rest.issues.createComment({
        owner: repo.owner.login,
        repo: repo.name,
        issue_number: issue.number,
        body: reminderBody,
    });
    console.log("[Beginner Bot] Reminder posted successfully.");
  }
};