// .github/scripts/bot-merge-conflict.js

const BOT_SIGNATURE = '[MergeConflictBotSignature-v1]';

module.exports = async ({ github, context, core }) => {
  const { owner, repo } = context.repo;

  // Validate event context
  if (context.eventName !== 'push' && context.eventName !== 'pull_request_target') {
    console.log(`Unsupported event type: ${context.eventName}. Skipping.`);
    return;
  }

  // Check for dry-run mode
  const dryRun = process.env.DRY_RUN === 'true';

  // Fetch PR with retry logic for unknown state
  async function getPrWithRetry(prNumber) {
    for (let i = 0; i < 10; i++) {
      const { data: pr } = await github.rest.pulls.get({
        owner, repo, pull_number: prNumber
      });

      if (pr.mergeable_state !== 'unknown') return pr;

      console.log(`PR #${prNumber} state is 'unknown'. Retrying (${i+1}/10)...`);
      await new Promise(r => setTimeout(r, 2000));
    }
    const { data: pr } = await github.rest.pulls.get({ owner, repo, pull_number: prNumber });
    if (pr.mergeable_state === 'unknown') {
      console.warn(`PR #${prNumber} state still 'unknown' after 10 retries.`);
    }
    return pr;
  }

  // Post comment
  async function notifyUser(prNumber) {
    const { data: comments } = await github.rest.issues.listComments({
      owner, repo, issue_number: prNumber,
    });

    if (comments.some(c => c.body.includes(BOT_SIGNATURE))) {
      console.log(`Already commented on PR #${prNumber}. Skipping.`);
      return;
    }

    const body = `Hi, this is MergeConflictBot.\nYour pull request cannot be merged because it contains **merge conflicts**.\n\nPlease resolve these conflicts locally and push the changes.\n\nTo assist you, please read:\n- [Resolving Merge Conflicts](https://github.com/${owner}/${repo}/blob/main/docs/sdk_developers/merge_conflicts.md)\n- [Rebasing Guide](https://github.com/${owner}/${repo}/blob/main/docs/sdk_developers/rebasing.md)\n\nThank you for contributing!\n<!-- \nFrom the Hiero Python SDK Team\n${BOT_SIGNATURE} -->`;

    if (dryRun) {
      console.log(`[DRY RUN] Would post comment to PR #${prNumber}: ${body}`);
      return;
    }

    await github.rest.issues.createComment({
      owner, repo, issue_number: prNumber, body: body
    });
  }

  // Set commit status
  async function setCommitStatus(sha, state, description) {
    if (dryRun) {
      console.log(`[DRY RUN] Would set status for ${sha}: ${state} - ${description}`);
      return;
    }

    await github.rest.repos.createCommitStatus({
      owner, repo, sha: sha, state: state,
      context: 'Merge Conflict Detector',
      description: description,
      target_url: `${process.env.GITHUB_SERVER_URL}/${owner}/${repo}/actions/runs/${context.runId}`
    });
  }

  // Main
  let prsToCheck = [];

  // Push to main
  if (context.eventName === 'push') {
    console.log("Triggered by Push to Main. Fetching all open PRs...");
    const openPrs = await github.paginate(github.rest.pulls.list, {
      owner, repo, state: 'open', base: 'main', per_page: 100
    });
    prsToCheck = openPrs.map(pr => pr.number);
  }
  // PR update
  else {
    console.log("Triggered by PR update.");
    if (!context.payload.pull_request?.number) {
      core.setFailed('Missing pull_request data in event payload');
      return;
    }
    prsToCheck.push(context.payload.pull_request.number);
  }

  for (const prNumber of prsToCheck) {
    try {
      console.log(`Checking PR #${prNumber}...`);
      const pr = await getPrWithRetry(prNumber);

      if (pr.mergeable_state === 'unknown') {
        console.log(`PR #${prNumber} state is still 'unknown'. Skipping conflict check.`);
        continue;
      }

      if (pr.mergeable_state === 'dirty') {
        console.log(`Conflict detected in PR #${prNumber}`);
        await notifyUser(prNumber);

        // Push events: set commit status on PR head SHA
        // PR events: fail the workflow run (creates a check on the PR)
        if (context.eventName === 'push') {
          await setCommitStatus(pr.head.sha, 'failure', 'Conflicts detected with main');
        } else {
          core.setFailed(`Merge conflicts detected in PR #${prNumber}.`);
        }
      } else {
        console.log(`PR #${prNumber} is clean.`);
        // For push events, set success status; PR events rely on workflow run success
        if (context.eventName === 'push') {
          await setCommitStatus(pr.head.sha, 'success', 'No conflicts detected');
        }
      }
    } catch (error) {
      console.error(`Error checking PR #${prNumber}: ${error.message}`);
      if (context.eventName !== 'push') {
        throw error; // Re-throw for PR events to fail the workflow
      }
      // For push events, log and continue to check remaining PRs
    }
  }
};
