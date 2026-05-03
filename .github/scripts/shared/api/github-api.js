// ---------------------------------------------------------------------------
// GitHub API helpers
// ---------------------------------------------------------------------------

const { CONFIG } = require('../config');

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
  } catch {
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
  } catch {
    return null;
  }
}

module.exports = {
  fetchIssuesBatch,
  countClosedIssuesByAssignee,
};
