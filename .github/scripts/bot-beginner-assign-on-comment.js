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
      * Scans previous comments for a hidden marker: "<!-- beginner assign reminder -->".
      * If found -> Exits to avoid spamming the thread.
    - Action: Posts a comment with the hidden marker and instructions.

------------------------------------------------------------------------------
Parameters:
  - { github, context }: Standard objects provided by 'actions/github-script'.
==============================================================================
*/

const fs = require("fs");

const SPAM_LIST_PATH = ".github/spam-list.txt";
const REQUIRED_GFI_COUNT = 1;
const GFI_LABEL = 'Good First Issue';
const BEGINNER_GUARD_MARKER = '<!-- beginner-gfi-guard -->';

function isSafeSearchToken(value) {
  return typeof value === 'string' && /^[a-zA-Z0-9._/-]+$/.test(value);
}

async function countCompletedGfiIssues(github, owner, repo, username) {
  if (
    !isSafeSearchToken(owner) ||
    !isSafeSearchToken(repo) ||
    !isSafeSearchToken(username)
  ) {
    return null;
  }

  const searchQuery = [
    `repo:${owner}/${repo}`,
    `label:"${GFI_LABEL}"`,
    'is:issue',
    'is:closed',
    `assignee:${username}`,
  ].join(' ');

  const result = await github.graphql(
    `
    query ($query: String!) {
      search(type: ISSUE, query: $query) {
        issueCount
      }
    }
    `,
    { query: searchQuery }
  );

  return result?.search?.issueCount ?? 0;
}

module.exports = async ({ github, context }) => {
  try {
    const { payload } = context;
    const issue = payload.issue;
    const comment = payload.comment;
    const repo = payload.repository;

    // 1. Basic Validation
    if (!issue || !comment || !repo || issue.pull_request) {
      console.log("[Beginner Bot] Invalid payload or PR comment. Exiting.");
      return;
    }

    // 1.1 Bot Check (Fix 2: Defensive Check)
    if (comment.user?.type === "Bot") {
      console.log(`[Beginner Bot] Commenter @${comment.user.login} is a bot. Exiting.`);
      return;
    }

    // 2. Label Check (Fix 2: Defensive Check)
    const hasBeginnerLabel = Array.isArray(issue.labels) && issue.labels.some((label) => label.name === "beginner");
    if (!hasBeginnerLabel) {
      console.log(`[Beginner Bot] Issue #${issue.number} does not have 'beginner' label. Exiting.`);
      return;
    }

    // 3. Collaborator Check Helper
    async function isRepoCollaborator(username) {
      try {
        if (username === repo.owner.login) {
          console.log(`[Beginner Bot] User @${username} is the repo owner.`);
          return true;
        }

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
        return false;
      }
    }

    // NEW: Spam + Assignment Limit Helpers (Layered In)

    function isSpamUser(username) {
      if (!fs.existsSync(SPAM_LIST_PATH)) return false;

      const list = fs.readFileSync(SPAM_LIST_PATH, "utf8")
        .split("\n")
        .map(l => l.trim())
        .filter(l => l && !l.startsWith("#"));

      return list.includes(username);
    }

    async function getOpenAssignments(username) {
      const issues = await github.paginate(
        github.rest.issues.listForRepo,
        {
          owner: repo.owner.login,
          repo: repo.name,
          assignee: username,
          state: "open",
          per_page: 100,
        }
      );
      return issues.length;
    }

    const commenter = comment.user.login;

    // Fix 3: Validate comment body
    if (!comment.body) {
      console.log("[Beginner Bot] Comment body is empty. Exiting.");
      return;
    }

    const commentBody = comment.body.toLowerCase();
    const isAssignCommand = /(^|\s)\/assign(\s|$)/i.test(commentBody);

    // 4. Logic Branch
    if (isAssignCommand) {
      const completedGfiCount = await countCompletedGfiIssues(
        github,
        repo.owner.login,
        repo.name,
        commenter
      );

      if (completedGfiCount === null) {
        console.log("[Beginner Bot] Skipping GFI guard due to API error.");
        return;
      }

      if (completedGfiCount < REQUIRED_GFI_COUNT) {
        const comments = await github.rest.issues.listComments({
          owner: repo.owner.login,
          repo: repo.name,
          issue_number: issue.number,
        });

        if (!comments.data.some((c) => c.body?.includes(BEGINNER_GUARD_MARKER))) {
          await github.rest.issues.createComment({
            owner: repo.owner.login,
            repo: repo.name,
            issue_number: issue.number,
            body: `${BEGINNER_GUARD_MARKER}
👋 Hi @${commenter}! Thanks for your interest in contributing 💡

Before taking on a **beginner** issue, we ask contributors to complete at least one **Good First Issue** to get familiar with the workflow.

Please try a GFI first, then come back — we’ll be happy to assign this! 😊`,
          });
        }
        return;
      }
      
      // --- ASSIGNMENT LOGIC ---
      if (issue.assignees && issue.assignees.length > 0) {
        await github.rest.issues.createComment({
          owner: repo.owner.login,
          repo: repo.name,
          issue_number: issue.number,
          body: `👋 Hi @${commenter}, this issue is already assigned. Feel free to check other beginner issues!`,
        });
        return;
      }

      // Block spam users from beginner issues

      const spamUser = isSpamUser(commenter);

      if (spamUser) {
        console.log(`[Beginner Bot] Spam user @${commenter} attempted to assign to beginner issue. Blocked.`);

        try {
          await github.rest.issues.createComment({
            owner: repo.owner.login,
            repo: repo.name,
            issue_number: issue.number,
            body: `Hi @${commenter}, your account is currently restricted to **Good First Issues**. Please complete a Good First Issue or contact a maintainer to have restrictions reviewed.`,
          });
        } catch (error) {
          console.error(`[Beginner Bot] Failed to post spam restriction message: ${error.message}`);
        }

        return;
      }

      // Enforce Assignment Limits

      const openCount = await getOpenAssignments(commenter);
      const maxAllowed = 2;

      console.log("[Beginner Bot] Limit check:", {
        commenter,
        openCount,
        spamUser,
        maxAllowed,
      });

      if (openCount >= maxAllowed) {
        const message = `👋 Hi @${commenter}, you already have **2 open assignments**. Please finish one before requesting another.`;

        try {
          await github.rest.issues.createComment({
            owner: repo.owner.login,
            repo: repo.name,
            issue_number: issue.number,
            body: message,
          });
        } catch (error) {
          console.error(`[Beginner Bot] Failed to post limit warning: ${error.message}`);
        }

        return;
      }

      console.log(`[Beginner Bot] Assigning issue #${issue.number} to @${commenter}...`);

      // Fix 4: Granular Try/Catch for Assign API
      try {
        await github.rest.issues.addAssignees({
          owner: repo.owner.login,
          repo: repo.name,
          issue_number: issue.number,
          assignees: [commenter],
        });
        console.log(`[Beginner Bot] Successfully assigned.`);
      } catch (error) {
        console.error(`[Beginner Bot] Failed to assign issue: ${error.message}`);
      }

    } else {
      // --- REMINDER LOGIC ---

      if (issue.assignees && issue.assignees.length > 0) {
        console.log(`[Beginner Bot] Issue #${issue.number} is already assigned. Skipping reminder.`);
        return;
      }

      if (await isRepoCollaborator(commenter)) {
        console.log(`[Beginner Bot] Commenter @${commenter} is a repo collaborator. Skipping reminder.`);
        return;
      }

      // Fix 5: Updated Marker Text
      const REMINDER_MARKER = "<!-- beginner assign reminder -->";
      // FIX 6: Granular Try/Catch for List Comments API
      let comments;
      try {
        const { data } = await github.rest.issues.listComments({
          owner: repo.owner.login,
          repo: repo.name,
          issue_number: issue.number,
        });
        comments = data;
      } catch (error) {
        console.error(`[Beginner Bot] Failed to list comments: ${error.message}`);
        return; // Exit gracefully if we can't check for duplicates
      }

      if (comments.some((c) => c.body.includes(REMINDER_MARKER))) {
        console.log("[Beginner Bot] Reminder already exists on this issue. Skipping.");
        return;
      }

      console.log(`[Beginner Bot] Posting help reminder for @${commenter}...`);

      const reminderBody = `${REMINDER_MARKER}\n👋 Hi @${commenter}! If you'd like to work on this issue, please comment \`/assign\` to get assigned.`;

      // FIX 6: Granular Try/Catch for Create Comment API
      try {
        await github.rest.issues.createComment({
          owner: repo.owner.login,
          repo: repo.name,
          issue_number: issue.number,
          body: reminderBody,
        });
        console.log("[Beginner Bot] Reminder posted successfully.");
      } catch (error) {
        console.error(`[Beginner Bot] Failed to post reminder: ${error.message}`);
      }
    }

  } catch (error) {
    // Fix 1: Top-level error handling
    console.error("[Beginner Bot] Unexpected error:", {
      message: error.message,
      status: error.status,
      issue: context.payload?.issue?.number,
      comment: context.payload?.comment?.id
    });
  }
};
