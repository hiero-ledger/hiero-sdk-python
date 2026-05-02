// ---------------------------------------------------------------------------
// Eligibility resolution
// ---------------------------------------------------------------------------

const { CONFIG } = require('../config');
const { repoLabelFor } = require('../helpers/utils');
const { countClosedIssuesByAssignee } = require('../api/github-api');

// Fast path: user has already completed ≥1 issue at this level or higher
async function passesBypassCheck(github, homeRepo, username, candidate) {
  const atOrAbove = CONFIG.skillHierarchy.slice(CONFIG.skillHierarchy.indexOf(candidate));

  const counts = await Promise.all(
    atOrAbove.map(key => countClosedIssuesByAssignee(
      github, homeRepo.owner, homeRepo.repo, username,
      repoLabelFor(homeRepo, key), 1,
    ))
  );

  return counts.some(count => count !== null && count >= 1);
}

/**
 * Checks whether a contributor meets the prerequisite count for a given level.
 *
 * Unlike the bypass check, this verifies that the contributor has completed
 * enough issues at the *previous* level to formally qualify for the candidate.
 */
async function passesNormalCheck(github, homeRepo, username, prereq) {
  const count = await countClosedIssuesByAssignee(
    github, homeRepo.owner, homeRepo.repo, username,
    repoLabelFor(homeRepo, prereq.requiredLevel), prereq.requiredCount,
  );
  if (count === null) return null;
  return count >= prereq.requiredCount;
}

/**
 * Determines whether a contributor is eligible for a single candidate level.
 *
 * Two checks are tried in order:
 *   1. Floor level (no prerequisite) — always eligible.
 *   2. Bypass — has already closed ≥1 issue at this level or higher.
 *   3. Normal — has met the prerequisite count at the previous level.
 *
 * Returns null on API failure so the caller can conservatively skip the candidate.
 *
 * @param {import('@actions/github').GitHub} github
 * @param {object} homeRepo  - Home repo entry from CONFIG.repos.
 * @param {string} username  - GitHub login of the contributor.
 * @param {string} candidate - Canonical level key being evaluated.
 * @returns {Promise<boolean|null>} True if eligible, false if not, null on API failure.
 */
async function isEligibleFor(github, homeRepo, username, candidate) {
  const prereq = CONFIG.skillPrerequisites[candidate];

  // Floor level (gfi) has no prerequisite — always eligible as a floor.
  if (!prereq?.requiredLevel) return true;

  const bypass = await passesBypassCheck(github, homeRepo, username, candidate);
  if (bypass) return true;

  // null (API failure) is treated as false — caller skips conservatively.
  const normal = await passesNormalCheck(github, homeRepo, username, prereq);
  return normal === true;
}

/**
 * Determines the highest skill level a contributor is eligible for,
 * based solely on their *historical* closed issues (excludes this PR).
 *
 * Walks the hierarchy from highest to lowest and returns the first
 * level for which the contributor is eligible. The result acts as a
 * ceiling — recommendations will not exceed this level.
 *
 * The caller is responsible for adjusting this ceiling to account for
 * the current PR's completion (see adjustEligibilityForCurrentPR).
 *
 * @param {import('@actions/github').GitHub} github
 * @param {object} homeRepo - Home repo entry from CONFIG.repos.
 * @param {string} username - GitHub login of the contributor.
 * @returns {Promise<string>} Canonical level key of the eligibility ceiling.
 */
async function resolveEligibleLevel(github, homeRepo, username) {
  for (const candidate of [...CONFIG.skillHierarchy].reverse()) {
    const eligible = await isEligibleFor(github, homeRepo, username, candidate);
    // eligible === null means API failure — skip conservatively.
    if (eligible === true) return candidate;
  }
  return 'gfi';
}

/**
 * Adjusts the historical eligibility ceiling to include the current PR's completion.
 *
 * resolveEligibleLevel is intentionally blind to the PR being processed.
 * Without this adjustment, a contributor completing their very first GFI
 * would have an eligibility ceiling of 'gfi' and never see beginner issues.
 *
 * Logic: if the ceiling is at or below the completed level, bump it one step up.
 *
 * @param {string} completedKey - Canonical key of the level just completed.
 * @param {string} eligibleKey  - Historical ceiling from resolveEligibleLevel.
 * @returns {string} Adjusted ceiling key.
 */
function adjustEligibilityForCurrentPR(completedKey, eligibleKey) {
  const h           = CONFIG.skillHierarchy;
  const completedIdx = h.indexOf(completedKey);
  const eligibleIdx  = h.indexOf(eligibleKey);

  return eligibleIdx <= completedIdx
    ? h[Math.min(completedIdx + 1, h.length - 1)]
    : eligibleKey;
}

/**
 * Detects whether the current PR completion crossed the threshold into the next level.
 *
 * Checks if the contributor has reached *exactly* the required count for the next
 * level after this PR. Uses cap = requiredCount + 1 to avoid over-fetching.
 *
 * Example: beginner → intermediate requires 3 beginner completions.
 * If the search returns count === 3, this PR was the one that crossed the line.
 *
 * @param {import('@actions/github').GitHub} github
 * @param {object} homeRepo        - Home repo entry from CONFIG.repos.
 * @param {string} username        - GitHub login of the contributor.
 * @param {string} currentLevelKey - Canonical key of the level just completed.
 * @returns {Promise<string|null>} Canonical key of the unlocked level, or null.
 */
async function detectUnlockedLevel(github, homeRepo, username, currentLevelKey) {
  const hierarchy    = CONFIG.skillHierarchy;
  const currentIndex = hierarchy.indexOf(currentLevelKey);
  const nextKey      = hierarchy[currentIndex + 1] ?? null;

  if (!nextKey) return null;

  const nextPrereq = CONFIG.skillPrerequisites[nextKey];
  if (!nextPrereq?.requiredLevel || nextPrereq.requiredLevel !== currentLevelKey) return null;

  const count = await countClosedIssuesByAssignee(
    github, homeRepo.owner, homeRepo.repo, username,
    repoLabelFor(homeRepo, currentLevelKey), nextPrereq.requiredCount + 1,
  );

  if (count === null) return null;
  return count === nextPrereq.requiredCount ? nextKey : null;
}

module.exports = {
  passesBypassCheck,
  passesNormalCheck,
  isEligibleFor,
  resolveEligibleLevel,
  adjustEligibilityForCurrentPR,
  detectUnlockedLevel,
};
