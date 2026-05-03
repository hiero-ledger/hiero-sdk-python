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
 * @returns {Promise<boolean>} True if eligible, false otherwise (API failures treated as false).
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
    // false includes API failures (treated conservatively as ineligible)
    if (eligible === true) return candidate;
  }
  return CONFIG.skillHierarchy[0];
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
 * Computes next level metadata for unlock detection.
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
  if (!nextPrereq || nextPrereq.requiredLevel !== currentLevelKey) return null;

  return { nextKey, nextPrereq };
}

/**
 * Detects if the contributor just unlocked the next level.
 *
 * Trigger condition:
 *   completed count === requiredCount
 *
 * Uses a capped query (requiredCount + 1) for efficiency.
 *
 * @param {import('@actions/github').GitHub} github
 * @param {object} homeRepo
 * @param {string} username
 * @param {string} currentLevelKey
 * @returns {Promise<string|null>} unlocked level key
 */
async function detectUnlockedLevel(github, homeRepo, username, currentLevelKey) {
  const next = getNextLevelInfo(currentLevelKey);
  if (!next) return null;

  const { nextKey, nextPrereq } = next;

  const count = await countClosedIssuesByAssignee(
    github,
    homeRepo.owner,
    homeRepo.repo,
    username,
    repoLabelFor(homeRepo, currentLevelKey),
    nextPrereq.requiredCount + 1,
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
