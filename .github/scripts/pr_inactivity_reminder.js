// A script to remind PR authors of inactivity by posting a comment.

// DRY_RUN env var: any case-insensitive 'true' value will enable dry-run
const dryRun = (process.env.DRY_RUN || 'false').toString().toLowerCase() === 'true';

// Helper to resolve the head repo of a PR
function resolveHeadRepo(pr, defaultOwner, defaultRepo) {
  return {
    owner: pr.head.repo?.owner?.login || defaultOwner,
    repo: pr.head.repo?.name || defaultRepo,
  };
}

// Helper to get the last commit date of a PR
async function getLastCommitDate(github, pr, owner, repo) {
 const { owner: headRepoOwner, repo: headRepoName } = resolveHeadRepo(pr, owner, repo);
  try {
    const commitRes = await github.rest.repos.getCommit({
      owner: headRepoOwner,
      repo: headRepoName,
      ref: pr.head.sha,
    });
    const commit = commitRes.data?.commit ?? null;
    return new Date(commit?.author?.date || commit?.committer?.date || pr.created_at);
  } catch (getCommitErr) {
    console.log(`Failed to fetch head commit ${pr.head.sha} for PR #${pr.number}:`, getCommitErr.message || getCommitErr);
    return null; // Signal fallback needed
  }
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
    return comments.find(c => c.body && c.body.includes(marker)) || false;
  } catch (err) {
    console.log(`Failed to list comments for PR #${pr.number}:`, err.message || err);
    return null; // Prevent duplicate comment if we cannot check
  }
}

// Helper to post an inactivity comment
async function postInactivityComment(github, pr, owner, repo, marker, inactivityDays, discordLink, office_hours_calendar) {
  const comment = `${marker}
Hi @${pr.user.login},\n\nThis pull request has had no commit activity for ${inactivityDays} days. Are you still working on the issue? please push a commit to keep the PR active or it will be closed due to inactivity.
If you’re no longer able to work on this issue, please comment \`/unassign\` on the linked **issue** (not this pull request) to release it.
Reach out on discord or join our office hours if you need assistance.\n\n- ${discordLink}\n- ${office_hours_calendar} \n\nFrom the Python SDK Team`;
  if (dryRun) {
    console.log(`DRY-RUN: Would comment on PR #${pr.number} (${pr.html_url}) with body:\n---\n${comment}\n---`);
    return true;
  }

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
  const office_hours_calendar =`[Office Hours](https://zoom-lfx.platform.linuxfoundation.org/meetings/hiero?view=week)`; 
  // Unique marker so we can find the bot's own comment later.
  const marker = '<!-- pr-inactivity-bot-marker -->';

  if (dryRun) {
    console.log('Running in DRY-RUN mode: no comments will be posted.');
  }

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
    const inactivityDays = Math.floor((Date.now() - (lastCommitDate ? lastCommitDate.getTime() : new Date(pr.created_at).getTime())) / (1000 * 60 * 60 * 24));


    if (lastCommitDate > cutoff) {
      skippedCount++;
      console.log(`PR #${pr.number} has recent commit on ${lastCommitDate.toISOString()} - skipping`);
      continue;
    }

    // 2. Check for existing comment
    const existingBotComment = await hasExistingBotComment(github, pr, owner, repo, marker);
    if (existingBotComment) {
      skippedCount++;
      const idInfo = existingBotComment && existingBotComment.id ? existingBotComment.id : '(unknown)';
      console.log(`PR #${pr.number} already has an inactivity comment (id: ${idInfo}) - skipping`);
      continue;
    }

    // 3. Post inactivity comment
    const commented = await postInactivityComment(github, pr, owner, repo, marker, inactivityDays, discordLink, office_hours_calendar);
    if (commented) commentedCount++;
  }

  console.log("=== Summary ===");
  console.log(`PRs commented: ${commentedCount}`);
  console.log(`PRs skipped (existing comment present): ${skippedCount}`);
};
