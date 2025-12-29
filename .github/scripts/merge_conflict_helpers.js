// scripts/merge_conflict_helpers.js

const BOT_SIGNATURE = '[MergeConflictBotSignature-v1]';

module.exports = async ({ github, context, core }) => {
  const { owner, repo } = context.repo;

  // fetch PR with retry logic for unknown state
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
    return pr;
  }

  // post comment
  async function notifyUser(prNumber) {
    const { data: comments } = await github.rest.issues.listComments({
      owner, repo, issue_number: prNumber,
    });

    if (comments.some(c => c.body.includes(BOT_SIGNATURE))) {
      console.log(`Already commented on PR #${prNumber}. Skipping.`);
      return;
    }

    const body = `Hi, this is MergeConflictBot.\nYour pull request cannot be merged because it contains **merge conflicts**.\n\nPlease resolve these conflicts locally and push the changes.\n\nTo assist you, please read:\n- [Resolving Merge Conflicts](docs/sdk_developers/merge_conflicts.md)\n- [Rebasing Guide](docs/sdk_developers/rebasing.md)\n\nThank you for contributing!\nFrom the Hiero Python SDK Team\n\n${BOT_SIGNATURE}`;
    
    await github.rest.issues.createComment({
      owner, repo, issue_number: prNumber, body: body
    });
  }

  //set commit status
  async function setCommitStatus(sha, state, description) {
    await github.rest.repos.createCommitStatus({
      owner, repo, sha: sha, state: state,
      context: 'Merge Conflict Detector',
      description: description,
      target_url: `${process.env.GITHUB_SERVER_URL}/${owner}/${repo}/actions/runs/${context.runId}`
    });
  }

  //main
  let prsToCheck = [];

  //push to main
  if (context.eventName === 'push') {
    console.log("Triggered by Push to Main. Fetching all open PRs...");
    const { data: openPrs } = await github.rest.pulls.list({
      owner, repo, state: 'open', base: 'main'
    });
    prsToCheck = openPrs.map(pr => pr.number);
  } 
  //PR update
  else {
    console.log("Triggered by PR update.");
    prsToCheck.push(context.payload.pull_request.number);
  }

  let hasFailure = false;

  for (const prNumber of prsToCheck) {
    try {
      console.log(`Checking PR #${prNumber}...`);
      const pr = await getPrWithRetry(prNumber);

      if (pr.mergeable_state === 'dirty') {
        console.log(`Conflict detected in PR #${prNumber}`);
        await notifyUser(prNumber);

        if (context.eventName === 'push') {
          await setCommitStatus(pr.head.sha, 'failure', 'Conflicts detected with main');
        } else {
          core.setFailed(`Merge conflicts detected in PR #${prNumber}.`);
          hasFailure = true;
        }
      } else {
        console.log(`PR #${prNumber} is clean.`);
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
