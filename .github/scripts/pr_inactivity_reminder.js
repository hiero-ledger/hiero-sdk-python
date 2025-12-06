module.exports = async ({github, context}) => {
const inactivityThresholdDays = 10;
const cutoff = new Date(Date.now() - inactivityThresholdDays * 24 * 60 * 60 * 1000);
const owner = context.repo.owner;
const repo = context.repo.repo;

// Unique marker so we can find the bot's own comment later.
const marker = '<!-- pr-inactivity-bot-marker -->';

let commentedCount = 0;
let skippedCount = 0;

const prs = await github.paginate(github.rest.pulls.list, {
  owner,
  repo,
  state: 'open',
  per_page: 100,
});

for (const pr of prs) {
  let lastCommitDate;
  try {
    // Prefer fetching the head commit via the PR head SHA — this reliably gives the latest commit
    if (pr.head && pr.head.sha) {
      const headRepoOwner = pr.head.repo && pr.head.repo.owner ? pr.head.repo.owner.login : owner;
      const headRepoName = pr.head.repo && pr.head.repo.name ? pr.head.repo.name : repo;
      try {
        const commitRes = await github.rest.repos.getCommit({
          owner: headRepoOwner,
          repo: headRepoName,
          ref: pr.head.sha,
        });
        const commit = commitRes.data && commitRes.data.commit ? commitRes.data.commit : null;
        lastCommitDate = new Date(
          commit?.author?.date ||
          commit?.committer?.date ||
          pr.updated_at
        );
      } catch (getCommitErr) {
        // fallback to listing commits if getCommit fails (e.g., missing permissions on fork)
        console.log(`Failed to fetch head commit ${pr.head.sha} for PR #${pr.number}:`, getCommitErr.message || getCommitErr);
        const commits = await github.rest.pulls.listCommits({ owner, repo, pull_number: pr.number, per_page: 100 });
        if (commits.data && commits.data.length > 0) {
          const last = commits.data[commits.data.length - 1].commit;
          lastCommitDate = new Date(last?.author?.date || last?.committer?.date || pr.updated_at);
        } else {
          lastCommitDate = new Date(pr.updated_at);
        }
      }
    } else {
      // No head sha available - list commits and take the most recent
      const commits = await github.rest.pulls.listCommits({ owner, repo, pull_number: pr.number, per_page: 100 });
      if (commits.data && commits.data.length > 0) {
        const last = commits.data[commits.data.length - 1].commit;
        lastCommitDate = new Date(last?.author?.date || last?.committer?.date || pr.updated_at);
      } else {
        lastCommitDate = new Date(pr.updated_at);
      }
    }
  } catch (err) {
    console.log(`Failed to fetch commit info for PR #${pr.number}:`, err.message || err);
    lastCommitDate = new Date(pr.updated_at);
  }

  if (lastCommitDate > cutoff) {
    console.log(`PR #${pr.number} has recent commit on ${lastCommitDate.toISOString()} - skipping`);
    continue;
  }

  // Look for an existing bot comment using our unique marker.
  let existingBotComment = null;
  try {
    const comments = await github.paginate(github.rest.issues.listComments, {
      owner,
      repo,
      issue_number: pr.number,
      per_page: 100,
    });

    existingBotComment = comments.find(c => c.body && c.body.includes(marker));
  } catch (err) {
    console.log(`Failed to list comments for PR #${pr.number}:`, err.message || err);
    // If comments can't be fetched, skip to avoid duplicates/spam.
    continue;
  }

  if (existingBotComment) {
    skippedCount++;
    console.log(`PR #${pr.number} already has an inactivity comment (id: ${existingBotComment.id}) - skipping`);
    continue;
  }

  const comment = `${marker}
   Hi @${pr.user.login},\n\nThis pull request has had no commit activity for ${inactivityThresholdDays} days. Are you still working on the issue? If you are still working on it, please push a commit or let us know your status.\n\nFrom the Python SDK Team`;

  try {
    await github.rest.issues.createComment({
      owner,
      repo,
      issue_number: pr.number,
      body: comment,
    });
    commentedCount++;
    console.log(`Commented on PR #${pr.number} (${pr.html_url})`);
  } catch (commentErr) {
    console.log(`Failed to comment on PR #${pr.number}:`, commentErr);
  }
}

console.log("=== Summary ===");
console.log(`PRs commented: ${commentedCount}`);
console.log(`PRs skipped (existing comment present): ${skippedCount}`);
}