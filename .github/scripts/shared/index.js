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
  getRecommendedIssues,
  getHighestSkillLevelKey,
  buildRecommendationComment,
  postComment,
  alreadyCommented,
  extractLinkedIssueNumber,
  CONFIG,
};
