// core
const { getRecommendedIssues } = require('./core/recommendation');
const { runAssignmentFlow } = require('./core/issue-assign');

// helpers
const { getHighestSkillLevelKey } = require('./helpers/utils');
const { buildRecommendationComment } = require('./helpers/comment');
const {
  postComment,
  alreadyCommented,
  extractLinkedIssueNumber
} = require('./helpers/pr-helpers');

// config
const { CONFIG } = require('./config');

module.exports = {
  getRecommendedIssues,
  runAssignmentFlow,
  getHighestSkillLevelKey,
  buildRecommendationComment,
  postComment,
  alreadyCommented,
  extractLinkedIssueNumber,
  CONFIG,
};
