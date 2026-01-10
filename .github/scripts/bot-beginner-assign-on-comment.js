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
  2. Ignores Pull Requests, Bots, and issues missing the "beginner" label.
  3. Detects if the user typed "/assign".
     - If YES: Assigns the user to the issue (if currently unassigned).
     - If NO: Checks if the user is an external contributor expressing interest.
       If so, it replies with instructions on how to use the assign command.

------------------------------------------------------------------------------
Flow: Detailed Technical Steps

1️⃣ Validation & filtering
    - Checks payload to ensure it is an Issue Comment (not a PR).
    - Checks if the commenter is a BOT (e.g., github-actions). If so, exits.
    - Checks if the issue has the specific label "beginner". If not, exits.

2️⃣ Collaborator Check (isRepoCollaborator)
    - Action: Checks if the user is a repository collaborator.
    - Logic:
      * Collaborator (204) -> Treated as Team Member (Bot ignores them).
      * Non-Collaborator (404) -> Treated as External Contributor (Bot helps them).

3️⃣ Logic Branch A: The "/assign" Command
    - Trigger: User comment matches regex /(^|\s)\/assign(\s|$)/i.
    - Check: Is the issue already assigned?
      * Yes -> Alert the user that it is taken.
      * No  -> API Call: Add commenter to 'assignees'.

4️⃣ Logic Branch B: The Helper Reminder
    - Trigger: Generic comment (e.g., "I want to work on this").
    - Condition 1: Issue must be unassigned.
    - Condition 2: Commenter must NOT be a Repo Collaborator.
    - Condition 3: Duplicate Check.
      * Scans previous comments for a hidden marker: "".
      * If found -> Exits to avoid spamming the thread.
    - Action: Posts a comment with the hidden marker and instructions.

------------------------------------------------------------------------------
Parameters:
  - { github, context }: Standard objects provided by 'actions/github-script'.
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

  // 1.1 Bot Check
  if (comment.user.type === "Bot") {
    console.log(`[Beginner Bot] Commenter @${comment.user.login} is a bot. Exiting.`);
    return;
  }

  // 2. Label Check
  const hasBeginnerLabel = issue.labels.some((label) => label.name === "beginner");
  if (!hasBeginnerLabel) {
    console.log(`[Beginner Bot] Issue #${issue.number} does not have 'beginner' label. Exiting.`);
    return;
  }

  // 3. Collaborator Check Helper
  // (Replaces the old 'hasTeamMemberAccess' function)
  async function isRepoCollaborator(username) {
    try {
      // 3a. Owner is always a collaborator
      if (username === repo.owner.login) {
          console.log(`[Beginner Bot] User @${username} is the repo owner.`);
          return true;
      }

      // 3b. Check API for collaborator status
      // This endpoint returns 204 if user is a collaborator, 404 if not.
      await github.rest.repos.checkCollaborator({
        owner: repo.owner.login,
        repo: repo.name,
        username: username,
      });
      
      console.log(`[Beginner Bot] User @${username} is a confirmed repo collaborator.`);
      return true;
    } catch (error) {
      if (error.status === 404) {
        console.log(`[Beginner Bot] User @${username} is NOT a collaborator (External Contributor).`);
        return false;
      }
      
      console.log(`[Beginner Bot] Error checking collaborator status for @${username}: ${error.message}`);
      // Fail safe: If we can't check, assume FALSE to be helpful to the user.
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
        await github.rest.issues.createComment({
            owner: repo.owner.login,
            repo: repo.name,
            issue_number: issue.number,
            body: `👋 Hi @${commenter}, this issue is already assigned to someone else. Please find another "beginner" issue to work on!`,
        });
        
        return; // Exit after warning
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
    if (await isRepoCollaborator(commenter)) {
      console.log(`[Beginner Bot] Commenter @${commenter} is a repo collaborator. Skipping reminder.`);
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