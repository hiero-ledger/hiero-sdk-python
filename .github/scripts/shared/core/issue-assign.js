// .github/scripts/shared/issue-assign-core.js
//
// Shared engine for "/assign"-style comment automation across every
// difficulty level (beginner, Good First Issue, intermediate, advanced, ...).
//
// This file intentionally contains NO per-label copy or behavior — that all
// lives in .github/scripts/configs/assignment-levels.js. This module only
// knows how to run the generic flow:
//
//   1. Validate the webhook payload (real issue comment, not a bot, not a PR)
//   2. Confirm the issue carries the label this config cares about
//   3. If the comment is a plain "I'd like to help" message with no issue
//      assigned yet -> maybe post a one-time reminder to use `/assign`
//   4. If the comment contains `/assign`:
//        a. Enforce any prerequisite (e.g. "complete 1 GFI before taking a
//           beginner issue") — post a one-time guard comment if unmet
//        b. Refuse (with a comment) if the issue is already assigned
//        c. Enforce spam-list handling (hard block, or reduced limit)
//        d. Enforce the open-assignment cap
//        e. Assign the commenter
//        f. Run any post-assignment chain (mentor assignment, CodeRabbit
//           plan trigger, etc.) — each step is independent and non-fatal
//
// Adding a new difficulty level should never require touching this file.

const fs = require('fs');

function isSafeSearchToken(value) {
  return typeof value === 'string' && /^[a-zA-Z0-9._/-]+$/.test(value);
}

function commentRequestsAssignment(body) {
  return typeof body === 'string' && /(^|\s)\/assign(\s|$)/i.test(body);
}

function issueHasLabel(issue, label) {
  const target = label.toLowerCase();
  return Array.isArray(issue.labels) && issue.labels.some((l) => l.name?.toLowerCase() === target);
}

function getCurrentAssigneeMention(issue) {
  const login = issue?.assignees?.[0]?.login;
  return login ? `@${login}` : 'someone';
}

function isSpamUser(username, spamListPath) {
  if (!spamListPath || !fs.existsSync(spamListPath)) return false;

  const list = fs
    .readFileSync(spamListPath, 'utf8')
    .split('\n')
    .map((l) => l.trim())
    .filter((l) => l && !l.startsWith('#'));

  return list.includes(username);
}

async function getOpenAssignments({ github, owner, repo, username }) {
  const issues = await github.paginate(github.rest.issues.listForRepo, {
    owner,
    repo,
    assignee: username,
    state: 'open',
    per_page: 100,
  });
  return issues.length;
}

/**
 * Counts closed issues carrying `label` that were assigned to `username`.
 * Used to enforce prerequisites like "finish 1 GFI before taking a beginner
 * issue". Returns null (rather than throwing) on unsafe input or API error
 * so callers can choose to fail open.
 */
async function countCompletedIssuesWithLabel({ github, owner, repo, username, label }) {
  if (!isSafeSearchToken(owner) || !isSafeSearchToken(repo) || !isSafeSearchToken(username)) {
    return null;
  }

  const searchQuery = [
    `repo:${owner}/${repo}`,
    `label:"${label}"`,
    'is:issue',
    'is:closed',
    `assignee:${username}`,
  ].join(' ');

  try {
    const result = await github.graphql(
      `
      query ($searchQuery: String!) {
        search(type: ISSUE, query: $searchQuery) {
          issueCount
        }
      }
      `,
      { searchQuery }
    );
    return result?.search?.issueCount ?? 0;
  } catch (error) {
    console.error('[assign-bot] countCompletedIssuesWithLabel failed:', {
      owner,
      repo,
      username,
      label,
      message: error.message,
    });
    return null;
  }
}

async function isRepoCollaborator({ github, owner, repo, username }) {
  if (username === owner) {
    console.log(`[assign-bot] @${username} is the repo owner — treated as collaborator.`);
    return true;
  }

  try {
    const response = await github.rest.repos.getCollaboratorPermissionLevel({ owner, repo, username });
    const permission = response?.data?.permission;
    const isTeamMember = ['admin', 'write', 'maintain', 'read'].includes(permission);
    console.log('[assign-bot] isRepoCollaborator:', { username, permission, isTeamMember });
    return isTeamMember;
  } catch (error) {
    if (error?.status === 401 || error?.status === 403 || error?.status === 404) {
      console.log('[assign-bot] isRepoCollaborator: not a collaborator', { username, status: error.status });
      return false;
    }
    // Unexpected error talking to the API — fail closed (don't treat as collaborator)
    // but don't let it crash the whole run.
    console.error('[assign-bot] isRepoCollaborator: unexpected error', { username, message: error.message });
    return false;
  }
}

async function postComment({ github, owner, repo, issueNumber, body }, logLabel) {
  try {
    await github.rest.issues.createComment({ owner, repo, issue_number: issueNumber, body });
    console.log(`[assign-bot] Posted comment: ${logLabel}`);
  } catch (error) {
    console.error(`[assign-bot] Failed to post comment (${logLabel}):`, { message: error.message });
  }
}

async function fetchAllComments({ github, owner, repo, issueNumber }) {
  return github.paginate(github.rest.issues.listComments, {
    owner,
    repo,
    issue_number: issueNumber,
    per_page: 100,
  });
}

/**
 * Runs chained post-assignment steps in order. Each step is:
 *   { name: string, requiresPrevious?: boolean, run: async (ctx) => void }
 * A step throwing is caught and logged; it never fails the overall run
 * (the human assignment has already succeeded by this point). Steps with
 * requiresPrevious=true are skipped if the prior step failed, mirroring the
 * original "only trigger CodeRabbit if mentor assignment succeeded" logic.
 */
async function runPostAssignChain(chain, ctx) {
  let previousSucceeded = true;
  for (const step of chain || []) {
    if (step.requiresPrevious && !previousSucceeded) {
      console.log(`[assign-bot] Skipping chained step "${step.name}" (previous step failed).`);
      continue;
    }
    try {
      await step.run(ctx);
      previousSucceeded = true;
      console.log(`[assign-bot] Chained step "${step.name}" succeeded.`);
    } catch (error) {
      previousSucceeded = false;
      console.error(`[assign-bot] Chained step "${step.name}" failed:`, {
        message: error.message,
        status: error.status,
      });
    }
  }
}

/**
 * Main entry point. `levelConfig` describes everything level-specific;
 * see configs/assignment-levels.js for the shape and examples.
 */
async function runAssignmentFlow({ github, context, levelConfig }) {
  const { payload } = context;
  const issue = payload.issue;
  const comment = payload.comment;
  const repo = payload.repository;

  if (!issue || !comment || !repo || issue.pull_request) {
    console.log('[assign-bot] Invalid payload or PR comment. Exiting.');
    return;
  }

  if (comment.user?.type === 'Bot') {
    console.log(`[assign-bot] Commenter @${comment.user?.login} is a bot. Exiting.`);
    return;
  }

  if (!comment.body) {
    console.log('[assign-bot] Comment body is empty. Exiting.');
    return;
  }

  if (!issueHasLabel(issue, levelConfig.label)) {
    console.log(`[assign-bot] Issue #${issue.number} does not have the "${levelConfig.label}" label. Exiting.`);
    return;
  }

  const owner = repo.owner.login;
  const repoName = repo.name;
  const commenter = comment.user.login;
  const issueNumber = issue.number;
  const isAssigned = Array.isArray(issue.assignees) && issue.assignees.length > 0;

  // ---- Branch A: plain comment, no /assign — maybe post a reminder ----
  if (!commentRequestsAssignment(comment.body)) {
    if (isAssigned) {
      console.log(`[assign-bot] Issue #${issueNumber} already assigned. Skipping reminder.`);
      return;
    }

    if (await isRepoCollaborator({ github, owner, repo: repoName, username: commenter })) {
      console.log(`[assign-bot] @${commenter} is a collaborator. Skipping reminder.`);
      return;
    }

    let comments;
    try {
      comments = await fetchAllComments({ github, owner, repo: repoName, issueNumber });
    } catch (error) {
      console.error('[assign-bot] Failed to list comments for reminder check:', { message: error.message });
      return;
    }

    const reminderAlreadyPosted = comments.some((c) => c.body?.includes(levelConfig.reminderMarker));
    if (reminderAlreadyPosted) {
      console.log('[assign-bot] Reminder already posted. Skipping.');
      return;
    }

    const body = `${levelConfig.reminderMarker}\n${levelConfig.reminderMessageBuilder(commenter)}`;
    await postComment({ github, owner, repo: repoName, issueNumber, body }, 'assign reminder');
    return;
  }

  // ---- Branch B: /assign command ----

  // Prerequisite gate (e.g. "must complete 1 GFI before taking a beginner issue")
  if (levelConfig.prerequisite) {
    const { label: prereqLabel, count: requiredCount, guardMarker, guardMessageBuilder } = levelConfig.prerequisite;

    const completedCount = await countCompletedIssuesWithLabel({
      github,
      owner,
      repo: repoName,
      username: commenter,
      label: prereqLabel,
    });

    console.log('[assign-bot] Prerequisite check:', { commenter, prereqLabel, requiredCount, completedCount });

    if (completedCount === null) {
      console.log('[assign-bot] Skipping prerequisite guard due to API error (fail open).');
    } else if (completedCount < requiredCount) {
      let comments;
      try {
        comments = await fetchAllComments({ github, owner, repo: repoName, issueNumber });
      } catch (error) {
        console.error('[assign-bot] Failed to list comments for guard check:', { message: error.message });
        return;
      }

      const guardAlreadyPosted = comments.some((c) => c.body?.includes(guardMarker));
      if (!guardAlreadyPosted) {
        const body = `${guardMarker}\n${guardMessageBuilder(commenter, { owner, repo: repoName })}`;
        await postComment({ github, owner, repo: repoName, issueNumber, body }, 'prerequisite guard');
      }
      return;
    }
  }

  // Already assigned?
  if (isAssigned) {
    const body = levelConfig.alreadyAssignedMessageBuilder(commenter, issue, { owner, repo: repoName });
    await postComment({ github, owner, repo: repoName, issueNumber, body }, 'already-assigned notice');
    return;
  }

  // Spam handling
  const spamConfig = levelConfig.spam;
  const spamUser = spamConfig ? isSpamUser(commenter, spamConfig.listPath) : false;

  if (spamUser && spamConfig.behavior === 'block') {
    console.log(`[assign-bot] Spam user @${commenter} blocked from "${levelConfig.label}" issues.`);
    const body = spamConfig.blockedMessageBuilder(commenter);
    await postComment({ github, owner, repo: repoName, issueNumber, body }, 'spam restriction notice');
    return;
  }

  // Open-assignment cap (spam users may get a reduced cap instead of a hard block)
  const maxAllowed =
    spamUser && spamConfig?.behavior === 'limit' ? spamConfig.limitTo : levelConfig.maxOpenAssignments;

  const openCount = await getOpenAssignments({ github, owner, repo: repoName, username: commenter });
  console.log('[assign-bot] Limit check:', { commenter, openCount, spamUser, maxAllowed });

  if (openCount >= maxAllowed) {
    const body = levelConfig.limitMessageBuilder(commenter, { maxAllowed, spamLimited: spamUser && spamConfig?.behavior === 'limit' });
    await postComment({ github, owner, repo: repoName, issueNumber, body }, 'limit warning');
    return;
  }

  // Assign
  try {
    await github.rest.issues.addAssignees({ owner, repo: repoName, issue_number: issueNumber, assignees: [commenter] });
    console.log(`[assign-bot] Assigned #${issueNumber} to @${commenter}.`);
  } catch (error) {
    console.error('[assign-bot] Failed to assign issue:', { message: error.message });
    return;
  }

  // Post-assignment chain (mentor assignment, CodeRabbit plan, etc.)
  await runPostAssignChain(levelConfig.postAssignChain, {
    github,
    context,
    owner,
    repo: repoName,
    issue,
    issueNumber,
    assignee: { login: commenter, type: 'User' },
  });
}

module.exports = {
  runAssignmentFlow,
  isSafeSearchToken,
  commentRequestsAssignment,
  issueHasLabel,
  getCurrentAssigneeMention,
  isSpamUser,
  getOpenAssignments,
  countCompletedIssuesWithLabel,
  isRepoCollaborator,
};
