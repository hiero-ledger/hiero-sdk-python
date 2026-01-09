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
    // CHANGE THIS LINE: Use a unique HTML comment string
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