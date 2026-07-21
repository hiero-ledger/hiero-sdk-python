// ---------------------------------------------------------------------------
// GitHub API helpers
// ---------------------------------------------------------------------------

const { CONFIG } = require('../config');
const { isSafeSearchToken } = require("../helpers/validation");

/**
 * Counts closed issues historically assigned to a contributor at a given label,
 * capped at `cap` to limit API result size.
 *
 * Uses the search API rather than listForRepo because GitHub drops assignee
 * metadata from closed issues in the standard list endpoint.
 *
 * @param {import('@actions/github').GitHub} github
 * @param {string} owner       - Repo owner.
 * @param {string} repo        - Repo name.
 * @param {string} username    - GitHub login of the contributor.
 * @param {string} labelString - Repo-specific label string to filter by.
 * @param {number} cap - Maximum number of results to fetch (first page only, capped at 100).
 * @returns {Promise<number|null>} Number of fetched matching issues (not total count), or null on API failure.
 */
async function countClosedIssuesByAssignee(github, owner, repo, username, labelString, cap) {
  try {
    const { data } = await github.rest.search.issuesAndPullRequests({
      q:        `repo:${owner}/${repo} is:issue is:closed assignee:${username} label:"${labelString}"`,
      per_page: Math.min(cap, 100),
    });
    return data.items.length;
  } catch (err) {
    console.warn(`[github-api] countClosedIssuesByAssignee failed for ${username} in ${owner}/${repo}: ${err.message}`);
    return null;
  }
}

/**
 * Fetches a batch of open, unassigned issues from a repo, sorted oldest-first.
 * Intentionally broad — label filtering happens client-side in filterIssuesByLevel
 * to avoid one search call per skill level per repo.
 *
 * @param {import('@actions/github').GitHub} github
 * @param {object} repoConfig - Repo entry from CONFIG.repos.
 * @returns {Promise<Array<object>|null>} Issue array, or null on API failure.
 */
async function fetchIssuesBatch(github, repoConfig) {
  try {
    const query = [
      `repo:${repoConfig.owner}/${repoConfig.repo}`,
      'is:issue',
      'is:open',
      'no:assignee',
    ].join(' ');

    const { data } = await github.rest.search.issuesAndPullRequests({
      q:        query,
      per_page: CONFIG.fetchPerPage,
      sort:     'created',
      order:    'asc',
    });

    return data.items ?? [];
  } catch (err) {
    console.warn(`[github-api] fetchIssuesBatch failed for ${repoConfig.owner}/${repoConfig.repo}: ${err.message}`);
    return null;
  }
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
 * Counts closed issues carrying `label` (in the given repo) assigned to
 * `username`. Returns null (rather than throwing) on unsafe input or API
 * error so callers can choose to fail open.
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
    console.error('[github-api] countCompletedIssuesWithLabel failed:', {
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
    console.log(`[github-api] @${username} is the repo owner — treated as collaborator.`);
    return true;
  }

  try {
    const response = await github.rest.repos.getCollaboratorPermissionLevel({ owner, repo, username });
    const permission = response?.data?.permission;
    const isTeamMember = ['admin', 'write', 'maintain', 'read'].includes(permission);
    console.log('[github-api] isRepoCollaborator:', { username, permission, isTeamMember });
    return isTeamMember;
  } catch (error) {
    if (error?.status === 401 || error?.status === 403 || error?.status === 404) {
      console.log('[github-api] isRepoCollaborator: not a collaborator', { username, status: error.status });
      return false;
    }
    console.error('[github-api] isRepoCollaborator: unexpected error', { username, message: error.message });
    return false;
  }
}

async function postComment({ github, owner, repo, issueNumber, body }, logLabel) {
  try {
    await github.rest.issues.createComment({ owner, repo, issue_number: issueNumber, body });
    console.log(`[github-api] Posted comment: ${logLabel}`);
  } catch (error) {
    console.error(`[github-api] Failed to post comment (${logLabel}):`, { message: error.message });
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

async function assignIssue({
    github,
    owner,
    repo,
    issueNumber,
    username,
}) {
    await github.rest.issues.addAssignees({
        owner,
        repo,
        issue_number: issueNumber,
        assignees: [username],
    });
}

module.exports = {
  fetchIssuesBatch,
  countClosedIssuesByAssignee,
  getOpenAssignments,
  countCompletedIssuesWithLabel,
  isRepoCollaborator,
  postComment,
  fetchAllComments,
  assignIssue,
};
