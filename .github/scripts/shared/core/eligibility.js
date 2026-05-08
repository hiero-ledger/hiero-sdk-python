// ---------------------------------------------------------------------------
// Eligibility resolution
// ---------------------------------------------------------------------------

const { CONFIG } = require('../config');
const { repoLabelFor } = require('../helpers/utils');
const { countClosedIssuesByAssignee } = require('../api/github-api');

/**
 * Fast-path eligibility check.
 *
 * A contributor is considered eligible for `candidate` if they have already
 * completed at least one issue at that level OR any higher level.
 *
 * This avoids forcing strict progression when the user already has experience.
 *
 * @param {import('@actions/github').GitHub} github
 * @param {object} homeRepo
 * @param {string} username
 * @param {string} candidate - Canonical level key
 * @returns {Promise<boolean>}
 */
async function passesBypassCheck(github, homeRepo, username, candidate) {
  const idx = CONFIG.skillHierarchy.indexOf(candidate);
  if (idx === -1) return false;
  const atOrAbove = CONFIG.skillHierarchy.slice(idx);

  for (const key of atOrAbove) {
    const count = await countClosedIssuesByAssignee(
      github, homeRepo.owner, homeRepo.repo, username,
      repoLabelFor(homeRepo, key), 1,
    );
    if (count !== null && count >= 1) return true;
  }
  return false;
}

/**
 * Checks whether a contributor meets the prerequisite count for a level.
 *
 * This enforces the normal progression rules:
 * e.g. "3 beginner issues required before intermediate".
 *
 * @param {import('@actions/github').GitHub} github
 * @param {object} homeRepo
 * @param {string} username
 * @param {{ requiredLevel: string, requiredCount: number }} prereq
 * @returns {Promise<boolean|null>} null = API failure
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
 * Checks are evaluated in order:
 *   1. Floor level (no prerequisite) — always eligible.
 *   2. Bypass — contributor already completed ≥1 issue at this level or higher.
 *   3. Normal progression — contributor met prerequisite count requirements.
 *
 * API failures are treated conservatively as ineligible.
 *
 * @param {import('@actions/github').GitHub} github
 * @param {object} homeRepo
 * @param {string} username
 * @param {string} candidate - Canonical level key being evaluated
 * @returns {Promise<boolean>}
 */
async function isEligibleFor(github, homeRepo, username, candidate) {
  const prereq = CONFIG.skillPrerequisites[candidate];

  // Entry-level floor (gfi) is always eligible.
  if (!prereq?.requiredLevel) return true;

  const bypass = await passesBypassCheck(
    github,
    homeRepo,
    username,
    candidate,
  );

  if (bypass) return true;

  // API failures are treated conservatively as false.
  const normal = await passesNormalCheck(
    github,
    homeRepo,
    username,
    prereq,
  );

  return normal === true;
}

/**
 * Resolves the highest level the contributor is historically eligible for.
 *
 * Historical eligibility intentionally excludes the current PR being processed.
 * The result acts as an eligibility ceiling for recommendations.
 *
 * The caller is responsible for projecting the current PR completion
 * via adjustEligibilityForCurrentPR().
 *
 * @param {import('@actions/github').GitHub} github
 * @param {object} homeRepo
 * @param {string} username
 * @returns {Promise<string>} Canonical level key
 */
async function resolveEligibleLevel(github, homeRepo, username) {
  for (const candidate of [...CONFIG.skillHierarchy].reverse()) {
    const eligible = await isEligibleFor(
      github,
      homeRepo,
      username,
      candidate,
    );

    // false includes API failures (treated conservatively)
    if (eligible === true) return candidate;
  }

  return CONFIG.skillHierarchy[0];
}

/**
 * Projects the contributor's eligibility ceiling after including
 * the current PR completion.
 *
 * resolveEligibleLevel() intentionally ignores the current PR.
 * Without this adjustment, contributors completing their first GFI
 * would never receive beginner recommendations.
 *
 * Logic:
 *   if eligible ceiling <= completed level
 *   => bump ceiling one level upward
 *
 * @param {string} completedKey - Level completed by current PR
 * @param {string} eligibleKey  - Historical eligibility ceiling
 * @returns {string} Adjusted eligibility ceiling
 */
function adjustEligibilityForCurrentPR(completedKey, eligibleKey) {
  const h = CONFIG.skillHierarchy;

  const completedIdx = h.indexOf(completedKey);
  const eligibleIdx = h.indexOf(eligibleKey);

  return eligibleIdx <= completedIdx
    ? h[Math.min(completedIdx + 1, h.length - 1)]
    : eligibleKey;
}

/**
 * Computes metadata about the next progression level.
 *
 * Ensures:
 *   - current level exists
 *   - next level exists
 *   - next level depends on current level
 *
 * @param {string} currentLevelKey
 * @returns {{ nextKey: string, nextPrereq: object } | null}
 */
function getNextLevelInfo(currentLevelKey) {
  const hierarchy = CONFIG.skillHierarchy;

  const currentIndex = hierarchy.indexOf(currentLevelKey);
  if (currentIndex === -1) return null;

  const nextKey = hierarchy[currentIndex + 1];
  if (!nextKey) return null;

  const nextPrereq = CONFIG.skillPrerequisites[nextKey];

  if (
    !nextPrereq ||
    nextPrereq.requiredLevel !== currentLevelKey
  ) {
    return null;
  }

  return { nextKey, nextPrereq };
}

/**
 * Detects whether the current PR completion unlocks the next level.
 *
 * GitHub search indexing may lag behind workflow execution, so counts are
 * treated as historical state and the current PR completion is projected
 * locally via +1.
 *
 * Example:
 *   intermediate requires 3 beginner completions
 *   historical beginner count = 2
 *   current PR completes another beginner issue
 *   projected count = 3 => unlock intermediate
 *
 * Uses a capped query for efficiency.
 *
 * @param {import('@actions/github').GitHub} github
 * @param {object} homeRepo
 * @param {string} username
 * @param {string} currentLevelKey
 * @returns {Promise<string|null>} unlocked level key
 */
async function detectUnlockedLevel(
  github,
  homeRepo,
  username,
  currentLevelKey,
) {
  const next = getNextLevelInfo(currentLevelKey);
  if (!next) return null;

  const { nextKey, nextPrereq } = next;

  const historicalCount = await countClosedIssuesByAssignee(
    github,
    homeRepo.owner,
    homeRepo.repo,
    username,
    repoLabelFor(homeRepo, currentLevelKey),
    nextPrereq.requiredCount,
  );

  if (historicalCount === null) return null;

  const projectedCount = historicalCount + 1;

  return projectedCount === nextPrereq.requiredCount
    ? nextKey
    : null;
}

module.exports = {
  passesBypassCheck,
  passesNormalCheck,
  isEligibleFor,
  resolveEligibleLevel,
  adjustEligibilityForCurrentPR,
  detectUnlockedLevel,
};
