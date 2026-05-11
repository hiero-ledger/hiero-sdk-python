// SPDX-License-Identifier: Apache-2.0
//
// helpers/permissions.js
//
// Permission level checks and approval counting.
//
// CRITICAL NOTE ON role_name vs permission:
//   getCollaboratorPermissionLevel returns TWO fields:
//     - permission (legacy): maps maintain → write, triage → read
//     - role_name (accurate): returns admin | maintain | write | triage | read
//
//   We MUST use role_name to distinguish maintainers from committers.
//   If we used permission, Sophie (Maintain role per MAINTAINERS.md) would
//   appear as 'write', and maintainerApprovals would always be 0.
//   PRs would be permanently stuck at queue:maintainers.
//
//   Phase 3 will replace this with team membership checks
//   (getMembershipForUserInOrg) for full accuracy.

const { getLatestReviewStates } = require('./reviews');

const permissionCache = new Map();

/**
 * Check the repository role for a given user.
 *
 * Uses role_name (not legacy permission) to correctly detect the maintain role.
 * Results are cached in memory to avoid redundant API calls during the cron run.
 *
 * @param {object} github   - Octokit instance
 * @param {string} owner    - Repository owner
 * @param {string} repo     - Repository name
 * @param {string} username - GitHub username
 * @returns {string} 'admin' | 'maintain' | 'write' | 'triage' | 'read' | 'none'
 */
async function getPermissionLevel(github, owner, repo, username) {
  const cacheKey = `${owner}/${repo}/${username}`;

  if (permissionCache.has(cacheKey)) {
    return permissionCache.get(cacheKey);
  }

  try {
    const { data } = await github.rest.repos.getCollaboratorPermissionLevel({
      owner,
      repo,
      username,
    });
    // CRITICAL: Use role_name, NOT permission.
    // The legacy 'permission' field maps maintain → write, triage → read.
    // role_name correctly returns: admin | maintain | write | triage | read
    const role = data.role_name || data.permission || 'none';
    permissionCache.set(cacheKey, role);
    return role;
  } catch (error) {
    if (error.status === 404) {
      // External contributor — not a collaborator
      permissionCache.set(cacheKey, 'none');
      return 'none';
    }
    // Log unexpected errors but don't crash the run
    const message = error instanceof Error ? error.message : String(error);
    console.log(`    ⚠ Permission check failed for ${username}: ${message}. Treating as "none".`);
    return 'none';
  }
}

/**
 * Count approvals on a PR, split by permission level.
 *
 * Returns three counters:
 *   - maintainerApprovals: admin or maintain (maps to CODEOWNERS maintainer teams)
 *   - coreApprovals: write (committers) and maintainers
 *   - softApprovals: triage, read, none, external contributors
 *
 * @param {object} github   - Octokit instance
 * @param {string} owner    - Repository owner
 * @param {string} repo     - Repository name
 * @param {number} prNumber - Pull request number
 * @param {{ maintainerApprovals: number, coreApprovals: number, softApprovals: number, anyApproval: number }}
 */
async function countApprovals(github, owner, repo, prNumber) {
  const latestStates = await getLatestReviewStates(github, owner, repo, prNumber);

  let maintainerApprovals = 0; // only maintainers
  let coreApprovals = 0; // anyone with write permission
  let softApprovals = 0;

  for (const [username, state] of latestStates) {
    if (state !== 'APPROVED') continue;

    const role = await getPermissionLevel(github, owner, repo, username);

    if (role === 'admin' || role === 'maintain') {
      maintainerApprovals++;
      coreApprovals++; // Maintainers also count as core
    } else if (role === 'write') {
      coreApprovals++; // Committers count as core
    } else {
      // triage, read, none, or any unexpected value → soft approval
      softApprovals++;
    }
  }

  return {
    maintainerApprovals,
    coreApprovals,
    softApprovals,
    anyApproval: coreApprovals + softApprovals,
  };
}

function clearPermissionCache() {
  permissionCache.clear();
}

module.exports = { getPermissionLevel, countApprovals, clearPermissionCache };
