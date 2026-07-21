// .github/scripts/shared/issue-assign-core.js
//
// Shared engine for issue-comment assignment automation.
//
// All repository-specific labels, skill levels, and prerequisites are
// configured in config.js.
//
// Handles:
//   • one-time reminders for contributors who express interest
//   • "/assign" requests
//   • prerequisite enforcement
//   • spam restrictions
//   • assignment limits
//   • issue assignment
//
// Flow:
//   1. Validate the issue comment event
//   2. Resolve the configured repository and skill level
//   3. If the comment is not "/assign", optionally post a one-time reminder
//   4. Otherwise:
//      • enforce prerequisites
//      • reject already-assigned issues
//      • apply spam restrictions
//      • enforce assignment limits
//      • assign the issue

const { CONFIG, LEVEL_KEYS } = require('../config.js');

const {
  getOpenAssignments,
  countCompletedIssuesWithLabel,
  isRepoCollaborator,
  postComment,
  fetchAllComments,
  assignIssue,
} = require('../api/github-api.js');

const {
  buildAlreadyAssignedComment,
  buildGuardComment,
  buildLimitComment,
  buildReminderComment,
  buildSpamBlockedComment,
  reminderMarkerFor,
  guardMarkerFor,
} = require('../helpers/comment.js');

const {
  isSpamUser,
  spamUsersBlocked,
  isSpamLimited,
  getAssignmentLimit,
} = require('../helpers/spam.js');

function commentRequestsAssignment(body) {
  return typeof body === 'string' && /(^|\s)\/assign(\s|$)/i.test(body);
}

function findRepoConfig(owner, repo) {
  return CONFIG.repos.find((r) => r.owner === owner && r.repo === repo) || null;
}

function findHomeRepoConfig() {
  return CONFIG.repos.find((r) => r.isHome) || CONFIG.repos[0];
}

/**
 * Given an issue's labels and a repo config, returns the matching canonical
 * level key (highest tier first, so an issue mistakenly double-labeled
 * resolves to the more restrictive level) or null if none match.
 */
function resolveLevelKey(issue, repoConfig) {
  const issueLabels = new Set((issue.labels || []).map((l) => l.name?.toLowerCase()).filter(Boolean));

  for (let i = CONFIG.skillHierarchy.length - 1; i >= 0; i -= 1) {
    const levelKey = CONFIG.skillHierarchy[i];
    const label = repoConfig.labels?.[levelKey];
    if (label && issueLabels.has(label.toLowerCase())) {
      return levelKey;
    }
  }
  return null;
}

// ---------------------------------------------------------------------------
// Main entry point
// ---------------------------------------------------------------------------

async function runAssignmentFlow({ github, context }) {
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

  const owner = repo.owner.login;
  const repoName = repo.name;
  const repoConfig = findRepoConfig(owner, repoName);

  if (!repoConfig) {
    console.log(`[assign-bot] ${owner}/${repoName} is not a configured repo. Exiting.`);
    return;
  }

  const levelKey = resolveLevelKey(issue, repoConfig);
  if (!levelKey) {
    console.log(`[assign-bot] Issue #${issue.number} has no recognized skill label. Exiting.`);
    return;
  }

  const levelConfig = CONFIG.skillPrerequisites[levelKey];
  const label = repoConfig.labels[levelKey];
  const commenter = comment.user.login;
  const issueNumber = issue.number;
  const isAssigned = Array.isArray(issue.assignees) && issue.assignees.length > 0;

  console.log(`[assign-bot] Issue #${issueNumber} in ${owner}/${repoName} matched level "${levelKey}".`);

  // ---- plain comment, no /assign — post a reminder ----

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

    const marker = reminderMarkerFor(levelKey);
    if (comments.some((c) => c.body?.includes(marker))) {
      console.log('[assign-bot] Reminder already posted. Skipping.');
      return;
    }

    const body = `${marker}\n${buildReminderComment(commenter)}`;
    await postComment({ github, owner, repo: repoName, issueNumber, body }, 'assign reminder');
    return;
  }

  // ---- /assign command ----

  // Prerequisite check, resolved against the HOME repo's history/labels.
  if (levelConfig.requiredLevel && levelConfig.requiredCount > 0) {
    const homeRepoConfig = findHomeRepoConfig();
    const prereqLabel = homeRepoConfig.labels[levelConfig.requiredLevel];
    const prereqDisplayName = CONFIG.skillPrerequisites[levelConfig.requiredLevel].displayName;

    const completedCount = await countCompletedIssuesWithLabel({
      github,
      owner: homeRepoConfig.owner,
      repo: homeRepoConfig.repo,
      username: commenter,
      label: prereqLabel,
    });

    console.log('[assign-bot] Prerequisite check:', {
      commenter,
      prereqLabel,
      requiredCount: levelConfig.requiredCount,
      completedCount,
    });

    if (completedCount === null) {
      console.log('[assign-bot] Skipping prerequisite guard due to API error (fail open).');
    } else if (completedCount < levelConfig.requiredCount) {
      let comments;
      try {
        comments = await fetchAllComments({ github, owner, repo: repoName, issueNumber });
      } catch (error) {
        console.error('[assign-bot] Failed to list comments for guard check:', { message: error.message });
        return;
      }

      const marker = guardMarkerFor(levelKey);
      if (!comments.some((c) => c.body?.includes(marker))) {
        const body = `${marker}\n${buildGuardComment(commenter, {
          owner,
          repo: repoName,
          prereqLabel,
          prereqDisplayName,
          requiredCount: levelConfig.requiredCount,
          currentDisplayName: levelConfig.displayName,
        })}`;
        await postComment({ github, owner, repo: repoName, issueNumber, body }, 'prerequisite guard');
      }
      return;
    }
  }

  // Already assigned?
  if (isAssigned) {
    const body = buildAlreadyAssignedComment(commenter, issue, { owner, repo: repoName, label });
    await postComment({ github, owner, repo: repoName, issueNumber, body }, 'already-assigned notice');
    return;
  }

  // Spam handling
  const spamUser = isSpamUser(commenter);

  if (spamUser && spamUsersBlocked(levelKey)) {
    console.log(`[assign-bot] Spam user @${commenter} blocked from "${levelKey}" issues.`);
    const gfiDisplayName = CONFIG.skillPrerequisites[LEVEL_KEYS.GFI].displayName;
    const body = buildSpamBlockedComment(commenter, { prereqDisplayName: gfiDisplayName });
    await postComment({ github, owner, repo: repoName, issueNumber, body }, 'spam restriction notice');
    return;
  }

  const maxAllowed = getAssignmentLimit(levelKey, spamUser);

  const openCount = await getOpenAssignments({ github, owner, repo: repoName, username: commenter });
  console.log('[assign-bot] Limit check:', { commenter, openCount, spamUser, maxAllowed });

  if (openCount >= maxAllowed) {
    const spamLimited = isSpamLimited(levelKey, spamUser);
    const body = buildLimitComment(commenter, { maxAllowed, spamLimited });
    await postComment({ github, owner, repo: repoName, issueNumber, body }, 'limit warning');
    return;
  }

  // Assign
  try {
    await assignIssue({
      github,
      owner,
      repo: repoName,
      issueNumber,
      username: commenter,
    });
  } catch (error) {
    console.error("[assign-bot] Failed to assign issue:", {
      message: error.message,
    });
  }
  return;

}

module.exports = {
  runAssignmentFlow,
};
