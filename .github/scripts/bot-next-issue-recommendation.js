// .github/scripts/bot-next-issue-recommendation.js
//
// Recommends issues to contributors after a PR is merged.
//
// Recommendation priority (per issue description):
//   1. One level above what they just completed, home repo
//   2. One level above, other repos
//   3. Same level, home repo
//   4. Same level, other repos
//   5. One level below (never below beginner, never GFI), home repo then other repos
//   6. Silent — nothing posted
//
// Eligibility history caps the ceiling: a contributor who just completed GFI
// cannot be recommended intermediate even if intermediate issues are available.
// The target level is driven by what they completed, bounded by eligibility.
//
// Each repo declares its own label strings since naming varies across repos.

const {
  CONFIG,
  getHighestSkillLevelKey,
  getRecommendedIssues,
  buildRecommendationComment,
  postComment,
  alreadyCommented,
  extractLinkedIssueNumber,
} = require('./shared');

// ---------------------------------------------------------------------------
// Main entry point
// ---------------------------------------------------------------------------

module.exports = async ({ github, context, core }) => {
  const { payload } = context;
  const prNumber = payload.pull_request?.number;
  const prBody   = payload.pull_request?.body ?? '';
  const username = payload.pull_request?.user?.login;
  const homeRepo = CONFIG.repos.find(r => r.isHome);

  if (!homeRepo) {
    core.setFailed('No home repo configured (missing isHome: true)');
    return;
  }

  if (!prNumber || !username) {
    core.info('Missing PR number or username, skipping');
    return;
  }

  core.info(`Processing PR #${prNumber} by @${username}`);

  const { owner, repo } = homeRepo;
  if (await alreadyCommented(github, owner, repo, prNumber)) {
    core.info('Recommendation already posted, skipping');
    return;
  }

  const issueNumber = extractLinkedIssueNumber(prBody);
  if (!issueNumber) {
    core.info('No linked issue found in PR body, skipping');
    return;
  }

  core.info(`Linked issue: #${issueNumber}`);

  let issue;
  try {
    const { data } = await github.rest.issues.get({
      owner, repo, issue_number: issueNumber,
    });
    issue = data;
  } catch (error) {
    core.warning(`Could not fetch issue #${issueNumber}: ${error.message}`);
    return;
  }

  const completedLevelKey = getHighestSkillLevelKey(issue, homeRepo);
  if (!completedLevelKey) {
    core.info(`Issue #${issueNumber} has no recognised skill level label, skipping`);
    return;
  }

  core.info(`Completed level: ${completedLevelKey}`);

  const completedDisplayName = CONFIG.skillPrerequisites[completedLevelKey]?.displayName ?? completedLevelKey;

  let result;
  try {
    result = await getRecommendedIssues(github, homeRepo, username, completedLevelKey, core);
  } catch (error) {
    core.error(`Error generating recommendations: ${error.message}`);
    return;
  }

  if (!result) {
    core.warning('Recommendation engine returned no result');
    return;
  }

  const { issues, fromRepo, unlockedLevelKey } = result;

  if (issues.length === 0) {
    if (unlockedLevelKey) {
      // Milestone crossed but no issues available — post the unlock banner on its own.
      const posted = await postComment(
        github, owner, repo, prNumber,
        buildRecommendationComment(username, [], completedDisplayName, unlockedLevelKey),
        core,
      );
      if (!posted) core.setFailed(`Failed to post milestone comment on PR #${prNumber}`);
    } else {
      core.info('No eligible issues found, staying silent');
    }
    return;
  }

  if (fromRepo && fromRepo !== `${owner}/${repo}`) {
    core.info(`Recommending from cross-repo: ${fromRepo}`);
  }

  const posted = await postComment(
    github, owner, repo, prNumber,
    buildRecommendationComment(username, issues, completedDisplayName, unlockedLevelKey),
    core,
  );

  if (!posted) {
    core.setFailed(`Failed to post recommendation comment on PR #${prNumber}`);
  }
};
