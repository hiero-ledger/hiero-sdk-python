// Helper to get the last commit date of a PR
async function fetchHeadCommitDate(github, pr, owner, repo) {
  const headRepoOwner = pr.head.repo?.owner?.login || owner;
  const headRepoName = pr.head.repo?.name || repo;
  try {
    const commitRes = await github.rest.repos.getCommit({
      owner: headRepoOwner,
      repo: headRepoName,
      ref: pr.head.sha,
    });
    const commit = commitRes.data?.commit;
    return commit?.author?.date || commit?.committer?.date || pr.updated_at;
  } catch (getCommitErr) {
    console.log(`Failed to fetch head commit ${pr.head.sha} for PR #${pr.number}:`, getCommitErr.message || getCommitErr);
    return null; // Signal fallback needed
  }
}
 // fallback to listing commits if getCommit fails (e.g., missing permissions on fork)
async function fetchLastPRCommitDate(github, pr, owner, repo) {
  const commits = await github.rest.pulls.listCommits({ owner, repo, pull_number: pr.number, per_page: 100 });
  if (commits.data?.length) {
    const last = commits.data[commits.data.length - 1].commit;
    return last?.author?.date || last?.committer?.date || pr.updated_at;
  }
  return pr.updated_at;
}

async function getLastCommitDate(github, pr, owner, repo) {
  // Prefer fetching the head commit via the PR head SHA — this reliably gives the latest commit
  if (pr.head && pr.head.sha) {
    const headCommitDate = await fetchHeadCommitDate(github, pr, owner, repo);
    if (headCommitDate) return new Date(headCommitDate);
    // If failed, fallback to PR commit list
    const fallbackCommitDate = await fetchLastPRCommitDate(github, pr, owner, repo);
    return new Date(fallbackCommitDate);
  }
  // If no head SHA, just get last PR commit
  const lastCommitDate = await fetchLastPRCommitDate(github, pr, owner, repo);
  return new Date(lastCommitDate);
}

// Look for an existing bot comment using our unique marker.
async function hasExistingBotComment(github, pr, owner, repo, marker) {
  try {
    const comments = await github.paginate(github.rest.issues.listComments, {
      owner,
      repo,
      issue_number: pr.number,
      per_page: 100,
    });
    return comments.find(c => c.body && c.body.includes(marker));
  } catch (err) {
    console.log(`Failed to list comments for PR #${pr.number}:`, err.message || err);
    return null; // Prevent duplicate comment if we cannot check
  }
}

// Helper to post an inactivity comment
async function postInactivityComment(github, pr, owner, repo, marker, inactivityThresholdDays, discordLink, office_hours_calender) {
  const comment = `${marker}
Hi @${pr.user.login},\n\nThis pull request has had no commit activity for ${inactivityThresholdDays} days. 
Are you still working on the issue? Reach out on discord or join our office hours if you need assistance.\n\n- ${discordLink}\n- ${office_hours_calender} \n\nFrom the Python SDK Team`;

  try {
    await github.rest.issues.createComment({
      owner,
      repo,
      issue_number: pr.number,
      body: comment,
    });
    console.log(`Commented on PR #${pr.number} (${pr.html_url})`);
    return true;
  } catch (commentErr) {
    console.log(`Failed to comment on PR #${pr.number}:`, commentErr);
    return false;
  }
}

// Main module function
module.exports = async ({github, context}) => {
  const inactivityThresholdDays = 10; // days of inactivity before commenting
  const cutoff = new Date(Date.now() - inactivityThresholdDays * 24 * 60 * 60 * 1000);
  const owner = context.repo.owner;
  const repo = context.repo.repo;
  const discordLink = `[Discord](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/discord.md)`;
  const office_hours_calender =`[Office Hours](https://zoom-lfx.platform.linuxfoundation.org/meetings/hiero?view=week)`; 
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
    // 1. Check inactivity
    const lastCommitDate = await getLastCommitDate(github, pr, owner, repo);
    if (lastCommitDate > cutoff) {
      console.log(`PR #${pr.number} has recent commit on ${lastCommitDate.toISOString()} - skipping`);
      continue;
    }

    // 2. Check for existing comment
    const existingBotComment = await hasExistingBotComment(github, pr, owner, repo, marker);
    if (existingBotComment) {
      skippedCount++;
      console.log(`PR #${pr.number} already has an inactivity comment (id: ${existingBotComment.id}) - skipping`);
      continue;
    }

    // 3. Post inactivity comment
    const commented = await postInactivityComment(github, pr, owner, repo, marker, inactivityThresholdDays, discordLink, office_hours_calender);
    if (commented) commentedCount++;
  }

  console.log("=== Summary ===");
  console.log(`PRs commented: ${commentedCount}`);
  console.log(`PRs skipped (existing comment present): ${skippedCount}`);
};