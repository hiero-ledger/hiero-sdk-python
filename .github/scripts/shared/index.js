// core
const { getRecommendedIssues } = require('./core/recommendation');

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
  // core
  getRecommendedIssues,
  // helpers
  getHighestSkillLevelKey,
  buildRecommendationComment,
  postComment,
  alreadyCommented,
  extractLinkedIssueNumber,
  // config
  CONFIG,
};
