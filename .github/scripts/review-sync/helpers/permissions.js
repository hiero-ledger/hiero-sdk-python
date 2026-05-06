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
//   appear as 'write', and maintainerApproval would always be 0.
//   PRs would be permanently stuck at queue:maintainers.
//
//   Phase 3 will replace this with team membership checks
//   (getMembershipForUserInOrg) for full accuracy.

const { getLatestReviewStates } = require('./reviews');

/**
 * Check the repository role for a given user.
 *
 * Uses role_name (not legacy permission) to correctly detect the maintain role.
 *
 * @param {object} github   - Octokit instance
 * @param {string} owner    - Repository owner
 * @param {string} repo     - Repository name
 * @param {string} username - GitHub username
 * @returns {string} 'admin' | 'maintain' | 'write' | 'triage' | 'read' | 'none'
 */
async function getPermissionLevel(github, owner, repo, username) {
  try {
    const { data } = await github.rest.repos.getCollaboratorPermissionLevel({
      owner,
      repo,
      username,
    });
    // CRITICAL: Use role_name, NOT permission.
    // The legacy 'permission' field maps maintain → write, triage → read.
    // role_name correctly returns: admin | maintain | write | triage | read
    return data.role_name || data.permission || 'none';
  } catch (error) {
    if (error.status === 404) {
      // External contributor — not a collaborator
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
 *   - maintainerApproval: admin or maintain (maps to CODEOWNERS maintainer teams)
 *   - writeApproval: write (committers)
 *   - softApproval: triage, read, none, external contributors
 *
 * @param {object} github   - Octokit instance
 * @param {string} owner    - Repository owner
 * @param {string} repo     - Repository name
 * @param {number} prNumber - Pull request number
 * @returns {{ maintainerApproval: number, writeApproval: number, softApproval: number, anyApproval: number }}
 */
async function countApprovals(github, owner, repo, prNumber) {
  const latestStates = await getLatestReviewStates(github, owner, repo, prNumber);

  let maintainerApproval = 0;
  let writeApproval = 0;
  let softApproval = 0;

  for (const [username, state] of latestStates) {
    if (state !== 'APPROVED') continue;

    const role = await getPermissionLevel(github, owner, repo, username);

    if (role === 'admin' || role === 'maintain') {
      maintainerApproval++;
    } else if (role === 'write') {
      writeApproval++;
    } else {
      // triage, read, none, or any unexpected value → soft approval
      softApproval++;
    }
  }

  return {
    maintainerApproval,
    writeApproval,
    softApproval,
    anyApproval: maintainerApproval + writeApproval + softApproval,
  };
}

module.exports = { getPermissionLevel, countApprovals };
