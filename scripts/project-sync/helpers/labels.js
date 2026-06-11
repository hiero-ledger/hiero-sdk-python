const { ALL_MANAGED_LABELS } = require('./constants');

/**
 * Ensure a single label exists in the repository.
 *
 * Silently handles 422 (label already exists — race condition or concurrent
 * run), matching the pattern in review-sync/helpers/labels.js.
 *
 * @param {object}  github  - Octokit instance
 * @param {string}  owner   - Repository owner
 * @param {string}  repo    - Repository name
 * @param {object}  label   - Label descriptor { name, color, description }
 * @param {boolean} dryRun  - If true, log without making API calls
 * @returns {Promise<void>}
 */
async function ensureLabel(github, owner, repo, label, dryRun) {
    try {
        await github.rest.issues.getLabel({ owner, repo, name: label.name });
        console.log(`  Label "${label.name}" already exists. Skipping creation.`);
    } catch (error) {
        if (error.status === 404) {
            if (dryRun) {
                console.log(`  [DRY RUN] Would create label "${label.name}" (#${label.color}).`);
                return;
            }
            try {
                await github.rest.issues.createLabel({
                    owner,
                    repo,
                    name: label.name,
                    color: label.color,
                    description: label.description,
                });
                console.log(`  Created label "${label.name}" (#${label.color}).`);
            } catch (createError) {
                // 422 = label already exists (race condition or concurrent run)
                if (createError.status === 422) {
                    console.log(`  Label "${label.name}" already exists (422). Skipping.`);
                } else {
                    throw createError;
                }
            }
        } else {
            throw error;
        }
    }
}

/**
 * Ensure all project-sync managed labels exist in the repository.
 *
 * Covers all priority and type labels defined in constants.js.
 * Called once at the start of the apply workflow.
 *
 * @param {object}  github  - Octokit instance
 * @param {string}  owner   - Repository owner
 * @param {string}  repo    - Repository name
 * @param {boolean} dryRun  - If true, log without making API calls
 * @returns {Promise<void>}
 */
async function ensureAllLabels(github, owner, repo, dryRun) {
    for (const label of ALL_MANAGED_LABELS) {
        await ensureLabel(github, owner, repo, label, dryRun);
    }
}

module.exports = { ensureLabel, ensureAllLabels };
