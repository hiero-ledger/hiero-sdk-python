// ---------------------------------------------------------------------------
// Label helpers
// ---------------------------------------------------------------------------

const { CONFIG } = require('../config');

function repoLabelFor(repoConfig, levelKey) {
  return repoConfig.labels[levelKey];
}

function hasLabel(issue, labelName) {
  const target = labelName.toLowerCase();
  return (issue.labels ?? []).some(l => l.name.toLowerCase() === target);
}

function filterIssuesByLevel(issues, levelKey, repoConfig) {
  const labelString = repoLabelFor(repoConfig, levelKey);
  return issues
    .filter(issue => hasLabel(issue, labelString))
    .slice(0, CONFIG.maxRecommendations);
}

function getHighestSkillLevelKey(issue, repoConfig) {
  return [...CONFIG.skillHierarchy]
    .reverse()
    .find(key => hasLabel(issue, repoLabelFor(repoConfig, key))) ?? null;
}

module.exports = {
  repoLabelFor,
  hasLabel,
  filterIssuesByLevel,
  getHighestSkillLevelKey,
};
