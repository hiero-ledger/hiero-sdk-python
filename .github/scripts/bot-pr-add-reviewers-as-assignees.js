// =============================================================================
// Add Reviewers as Assignees Bot
// =============================================================================
//
// This script automatically adds requested reviewers (individuals + expanded 
// team members) as assignees on a PR. Makes it easier for reviewers to find
// their PRs via the "Assigned to me" filter.
//
// Triggered by:
//   - pull_request review_requested event
//   - workflow_dispatch (for manual testing)
//
// Key behavior:
//   - Only adds users who aren't already assignees
//   - Expands teams with graceful fallback on permission/visibility issues
//   - Supports dry-run mode
//   - Batches assignee updates (GitHub limit = 10 per call)
//   - Comprehensive logging for debugging
//
// Called by: .github/workflows/bot-pr-add-reviewers-as-assignees.yml

/**
 * Checks if the script is running in dry-run mode.
 *
 * Returns true if DRY_RUN env var is set to "true" (case-insensitive).
 */
function isDryRun() {
  return /^true$/i.test(process.env.DRY_RUN || '');
}

/**
 * Main handler that adds requested reviewers (individuals + expanded team members)
 * as assignees on a Pull Request.
 *
 * @param {Object} params
 * @param {Object} params.github - GitHub Octokit client from actions/github-script
 * @param {Object} params.context - GitHub Actions context
 * @returns {Promise<void>}
 */
module.exports = async ({ github, context }) => {
  const dryRun = isDryRun();
  if (dryRun) {
    console.log('[reviewers-assignee] Running in DRY-RUN mode - no changes will be made');
  }

  try {
    let prNumber = context.payload.pull_request?.number;
    let owner = context.repo.owner;
    let repo = context.repo.repo;

    // Support workflow_dispatch with manual PR number
    if (context.eventName === 'workflow_dispatch' && context.payload.inputs?.pr_number !== undefined) {
      const manualPrNumber = Number(context.payload.inputs.pr_number);
      if (!Number.isInteger(manualPrNumber) || manualPrNumber <= 0) {
        console.log('[reviewers-assignee] Invalid PR number supplied. Skipping.');
        return;
      }
      prNumber = manualPrNumber;
    }
    if (!Number.isInteger(prNumber) || prNumber <= 0) {
      console.log('[reviewers-assignee] No PR number found. Skipping.');
      return;
    }

    console.log(`[reviewers-assignee] Processing PR #${prNumber} in ${owner}/${repo}`);

    // Fetch fresh PR data
    const { data: pr } = await github.rest.pulls.get({
      owner,
      repo,
      pull_number: prNumber
    });

    const requestedReviewers = pr.requested_reviewers || [];
    const requestedTeams = pr.requested_teams || [];
    const currentAssignees = new Set(pr.assignees?.map(a => a.login) || []);

    console.log(`[reviewers-assignee] Requested reviewers: ${requestedReviewers.length}, teams: ${requestedTeams.length}`);

    const usersToAssign = new Set();

    // Add individual reviewers
    for (const reviewer of requestedReviewers) {
      if (reviewer?.login && !currentAssignees.has(reviewer.login)) {
        usersToAssign.add(reviewer.login);
      }
    }

    // Expand teams with pagination
    for (const team of requestedTeams) {
      if (!team?.slug) continue;
      try {
        const members = await github.paginate(github.rest.teams.listMembersInOrg, {
          org: owner,
          team_slug: team.slug,
          per_page: 100
        });

        for (const member of members) {
          if (member?.login && !currentAssignees.has(member.login)) {
            usersToAssign.add(member.login);
          }
        }
        console.log(`[reviewers-assignee] Expanded team ${team.slug} → ${members.length} members`);
      } catch (error) {
        if (error?.status === 403 || error?.status === 404) {
          console.log(`[reviewers-assignee] Could not expand team ${team.slug} due to permissions/visibility: ${error.message}`);
          continue;
        }
        console.error(`[reviewers-assignee] Failed to expand team ${team.slug}: ${error.message}`);
        throw error;
      }
    }

    if (usersToAssign.size === 0) {
      console.log('[reviewers-assignee] No new users to assign. Done.');
      return;
    }

    const assigneesList = Array.from(usersToAssign);
    console.log(`[reviewers-assignee] Will assign: ${assigneesList.join(', ')}`);

    if (dryRun) {
      console.log('[reviewers-assignee] DRY-RUN: Would have added the above users as assignees');
      return;
    }

    // Add up to 10 assignees at a time
    const ASSIGNEE_BATCH_SIZE = 10;
    let addedCount = 0;
    let permissionDenied = false;
    for (let i = 0; i < assigneesList.length; i += ASSIGNEE_BATCH_SIZE) {
      const batch = assigneesList.slice(i, i + ASSIGNEE_BATCH_SIZE);
      try {
        await github.rest.issues.addAssignees({
          owner,
          repo,
          issue_number: prNumber,
          assignees: batch
        });
        addedCount += batch.length;
        console.log(`[reviewers-assignee] Added batch of ${batch.length} assignees`);
      } catch (error) {
        if (error?.status === 403) {
          permissionDenied = true;
          console.log('[reviewers-assignee] Skipping remaining assignment due to insufficient permissions');
          break;
        }
        console.error(`[reviewers-assignee] Failed to add assignees batch: ${error.message}`);
        throw error;   // Re-throw other errors
      }
    }

    console.log(
      permissionDenied
        ? `[reviewers-assignee] Added ${addedCount} reviewer(s) before permissions blocked further assignment on PR #${prNumber}`
        : `[reviewers-assignee] Successfully added ${addedCount} reviewer(s) as assignee(s) on PR #${prNumber}`
    );

  } catch (error) {
    console.error('[reviewers-assignee] Error:', error.message);
    if (error.status) console.error('Status:', error.status);
    throw error;
  }
};