// ---------------------------------------------------------------------------
// Core recommendation logic
// ---------------------------------------------------------------------------

const { CONFIG } = require('../config');
const { filterIssuesByLevel } = require('../helpers/utils');
const { fetchIssuesBatch } = require('../api/github-api');
const {
  resolveEligibleLevel,
  detectUnlockedLevel,
  adjustEligibilityForCurrentPR
} = require('./eligibility');

/**
 * Order: level up → same → level down (floored at beginner, capped by eligibility)
 * 
 * @param {string} completedLevelKey - Canonical key of the level just completed.
 * @param {string} eligibleLevelKey  - Adjusted eligibility ceiling.
 * @returns {number[]} Deduplicated, ordered array of hierarchy indices to try.
 */
function computeLevelStepIndices(completedLevelKey, eligibleLevelKey) {
  const h            = CONFIG.skillHierarchy;
  const completedIdx = h.indexOf(completedLevelKey);
  const eligibleIdx  = h.indexOf(eligibleLevelKey);
  const beginnerIdx  = h.indexOf('beginner');

  const levelUp   = completedIdx + 1 <= eligibleIdx ? completedIdx + 1 : null;
  const same      = completedIdx;
  const levelDown = Math.max(completedIdx - 1, beginnerIdx);

  return [...new Set([levelUp, same, levelDown].filter(i => i !== null))];
}

/**
 * Expand levels across repos (home repo first). GFI is never recommended.
 *
 * @param {string} completedLevelKey - Canonical key of the level just completed.
 * @param {string} eligibleLevelKey  - Adjusted eligibility ceiling.
 * @returns {Array<{ levelKey: string, repoConfig: object }>} Ordered search chain.
 */
function buildFallbackChain(completedLevelKey, eligibleLevelKey) {
  return computeLevelStepIndices(completedLevelKey, eligibleLevelKey)
    .flatMap(i => {
      const levelKey = CONFIG.skillHierarchy[i];
      // Hard block: GFI is entry-only and must never appear in recommendations.
      if (levelKey === 'gfi') return [];
      return CONFIG.repos.map(repoConfig => ({ levelKey, repoConfig }));
    });
}

/**
 * Fetch all repos once (parallel) to avoid duplicate API calls during fallback
 *
 * @param {import('@actions/github').GitHub} github
 * @param {object} core - @actions/core logger.
 * @returns {Promise<Map<string, Array|null>>} Map of "owner/repo" → issues or null.
 */
async function prefetchIssues(github, core) {
  const cache = new Map();

  await Promise.all(CONFIG.repos.map(async repoConfig => {
    const key    = `${repoConfig.owner}/${repoConfig.repo}`;
    const issues = await fetchIssuesBatch(github, repoConfig);
    if (issues === null) core.warning(`Failed to fetch from ${key}, skipping this repo in all steps`);
    cache.set(key, issues);
  }));

  return cache;
}

/**
 * Main recommendation engine.
 *
 * Steps:
 *   1. Resolve the historical eligibility ceiling and detect any milestone unlock
 *      in parallel (both need separate search calls, neither depends on the other).
 *   2. Adjust the eligibility ceiling to include the current PR (see adjustEligibilityForCurrentPR).
 *   3. Pre-fetch issues from all repos concurrently.
 *   4. Walk the fallback chain and return the first level+repo combination
 *      that yields at least one matching issue.
 *
 * Returns an empty issues array when no match is found — the caller decides
 * whether to post a milestone-only comment or stay silent.
 *
 * @param {import('@actions/github').GitHub} github
 * @param {object} homeRepo        - Home repo entry (CONFIG.repos[0]).
 * @param {string} username        - GitHub login of the contributor.
 * @param {string} completedLevelKey - Canonical key of the level just completed.
 * @param {object} core            - @actions/core logger.
 * @returns {Promise<{ issues: Array, fromRepo: string|null, unlockedLevelKey: string|null }>}
 */
async function getRecommendedIssues(github, homeRepo, username, completedLevelKey, core) {
  const [eligibleLevelKey, unlockedLevelKey] = await Promise.all([
    resolveEligibleLevel(github, homeRepo, username),
    detectUnlockedLevel(github, homeRepo, username, completedLevelKey),
  ]);

  const adjustedEligibleKey = adjustEligibilityForCurrentPR(completedLevelKey, eligibleLevelKey);
  core.info(`Completed: ${completedLevelKey}, Eligible ceiling: ${adjustedEligibleKey}, Unlocked: ${unlockedLevelKey ?? 'none'}`);

  const issueCache = await prefetchIssues(github, core);
  const chain      = buildFallbackChain(completedLevelKey, adjustedEligibleKey);

  for (const { levelKey, repoConfig } of chain) {
    const repoKey = `${repoConfig.owner}/${repoConfig.repo}`;
    const issues  = issueCache.get(repoKey);

    // Skip if the fetch failed (null) or the repo is missing from the cache (undefined).
    if (issues == null) continue;

    const picked = filterIssuesByLevel(issues, levelKey, repoConfig);
    if (picked.length > 0) {
      core.info(`Recommending ${levelKey} issues from ${repoKey}`);
      return { issues: picked, fromRepo: repoKey, unlockedLevelKey };
    }
  }

  core.info(`No eligible issues found for @${username}`);
  return { issues: [], fromRepo: null, unlockedLevelKey };
}

module.exports = {
  computeLevelStepIndices,
  buildFallbackChain,
  prefetchIssues,
  getRecommendedIssues,
};
