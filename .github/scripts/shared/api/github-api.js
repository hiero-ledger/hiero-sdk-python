// ---------------------------------------------------------------------------
// GitHub API helpers
// ---------------------------------------------------------------------------

const { CONFIG } = require('../config');
const { isValidSearchToken } = require("../helpers/validation");

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

/**
 * Returns the number of open issues currently assigned to `username` in the
 * given repository. Pull requests are excluded because they do not consume
 * assignment capacity. Returns null on API failure so callers can fail open.
 *
 * @param {object} params
 * @param {import('@actions/github').GitHub} params.github
 * @param {string} params.owner    - Repo owner.
 * @param {string} params.repo     - Repo name.
 * @param {string} params.username - GitHub login of the contributor.
 * @returns {Promise<number|null>} Count of open issue assignments, or null on failure.
 */
async function getOpenAssignments({ github, owner, repo, username }) {
  try {
    const issues = await github.paginate(github.rest.issues.listForRepo, {
      owner,
      repo,
      assignee: username,
      state: 'open',
      per_page: 100,
    });

    // listForRepo returns both issues and pull requests.
    // Only open issues should consume assignment capacity.
    return issues.filter((item) => !item.pull_request).length;
  } catch (error) {
    console.error('[github-api] getOpenAssignments failed:', {
      owner,
      repo,
      username,
      message: error.message,
    });

    return null;
  }
}

/**
 * Counts closed issues carrying `label` (in the given repo) assigned to
 * `username`. Returns null (rather than throwing) on unsafe input or API
 * error so callers can choose to fail open.
 *
 * @param {object} params
 * @param {import('@actions/github').GitHub} params.github
 * @param {string} params.owner    - Repo owner.
 * @param {string} params.repo     - Repo name.
 * @param {string} params.username - GitHub login of the contributor.
 * @param {string} params.label    - Label string to filter by.
 * @returns {Promise<number|null>} Issue count, or null on invalid input or API failure.
 */
async function countCompletedIssuesWithLabel({ github, owner, repo, username, label }) {
  if (!isValidSearchToken(owner) || !isValidSearchToken(repo) || !isValidSearchToken(username)) {
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

/**
 * Determines whether a user has repository collaborator access.
 *
 * Repository owners are always considered collaborators.
 * GitHub returns 204 when the user is a collaborator and 404 otherwise.
 * Unexpected API failures are treated as non-collaborator access.
 *
 * @param {object} params
 * @param {import('@actions/github').GitHub} params.github
 * @param {string} params.owner    - Repo owner.
 * @param {string} params.repo     - Repo name.
 * @param {string} params.username - GitHub login to check.
 * @returns {Promise<boolean>} True if the user is a collaborator, false otherwise.
 */
async function isRepoCollaborator({ github, owner, repo, username }) {
  if (username === owner) {
    console.log(`[github-api] @${username} is the repo owner — treated as collaborator.`);
    return true;
  }

  try {
    await github.rest.repos.checkCollaborator({
      owner,
      repo,
      username,
    });

    console.log('[github-api] isRepoCollaborator: collaborator', {
      username,
    });

    return true;
  } catch (error) {
    if (error?.status === 404) {
      console.log('[github-api] isRepoCollaborator: not a collaborator', {
        username,
      });
      return false;
    }

    console.error('[github-api] isRepoCollaborator: unexpected error', {
      username,
      status: error?.status,
      message: error.message,
    });

    return false;
  }
}

/**
 * Posts a comment on an issue or pull request via the GitHub REST API.
 * When `logLabel` is provided, logs the outcome to the console; when omitted,
 * stays silent so the caller owns all logging. Re-throws any API error either
 * way so callers can handle or propagate failures themselves.
 *
 * @param {object} params
 * @param {import('@actions/github').GitHub} params.github
 * @param {string} params.owner       - Repo owner.
 * @param {string} params.repo        - Repo name.
 * @param {number} params.issueNumber - Issue or PR number to comment on.
 * @param {string} params.body        - Markdown body of the comment.
 * @param {string} [logLabel]         - Optional human-readable label used in console output.
 * @returns {Promise<void>}
 * @throws {Error} Re-throws the Octokit error on API failure.
 */
async function postIssueComment({ github, owner, repo, issueNumber, body }, logLabel) {
  try {
    await github.rest.issues.createComment({ owner, repo, issue_number: issueNumber, body });
    if (logLabel) {
      console.log(`[github-api] Posted comment: ${logLabel}`);
    }
  } catch (error) {
    if (logLabel) {
      console.error(`[github-api] Failed to post comment (${logLabel}):`, { message: error.message });
    }
    throw error;
  }
}

/**
 * Fetches all comments on an issue or pull request, paginating automatically.
 *
 * @param {object} params
 * @param {import('@actions/github').GitHub} params.github
 * @param {string} params.owner       - Repo owner.
 * @param {string} params.repo        - Repo name.
 * @param {number} params.issueNumber - Issue or PR number.
 * @returns {Promise<Array<object>>} Array of comment objects from the GitHub API.
 */
async function fetchAllComments({ github, owner, repo, issueNumber }) {
  return github.paginate(github.rest.issues.listComments, {
    owner,
    repo,
    issue_number: issueNumber,
    per_page: 100,
  });
}

/**
 * Assigns a contributor to an issue.
 *
 * @param {object} params
 * @param {import('@actions/github').GitHub} params.github
 * @param {string} params.owner       - Repo owner.
 * @param {string} params.repo        - Repo name.
 * @param {number} params.issueNumber - Issue number to assign.
 * @param {string} params.username    - GitHub login of the contributor to assign.
 * @returns {Promise<void>}
 */
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
  postIssueComment,
  fetchAllComments,
  assignIssue,
};
