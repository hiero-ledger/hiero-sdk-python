// ---------------------------------------------------------------------------
// Label helpers
// ---------------------------------------------------------------------------

const { CONFIG } = require('../config');

/**
 * Returns the repo-specific label string for a given canonical level key.
 *
 * @param {object} repoConfig - Repo config containing label mappings.
 * @param {string} levelKey   - Canonical skill level (e.g., 'beginner').
 * @returns {string|null} Label string or null if not defined.
 */
function repoLabelFor(repoConfig, levelKey) {
  return repoConfig.labels[levelKey] ?? null;
}

function hasLabel(issue, labelName) {
  if (!labelName) return false;

  const target = labelName.toLowerCase();
  return (issue.labels ?? []).some(l => l.name?.toLowerCase() === target);
}

/**
 * Filters issues by a specific skill level and caps the result size.
 */
function filterIssuesByLevel(issues, levelKey, repoConfig) {
  const labelString = repoLabelFor(repoConfig, levelKey);
  if (!labelString) return [];

  return issues
    .filter(issue => hasLabel(issue, labelString))
    .slice(0, CONFIG.maxRecommendations);
}

/**
 * Determines the highest skill level label present on an issue.
 * Iterates from highest → lowest so the first match represents the ceiling.
 *
 * @param {object} issue
 * @param {object} repoConfig
 * @returns {string|null} Canonical level key or null if none found.
 */
function getHighestSkillLevelKey(issue, repoConfig) {
  return [...CONFIG.skillHierarchy]
    .reverse()
    .find(key => {
      const label = repoLabelFor(repoConfig, key);
      return label && hasLabel(issue, label);
    }) ?? null;
}

module.exports = {
  repoLabelFor,
  hasLabel,
  filterIssuesByLevel,
  getHighestSkillLevelKey,
};
