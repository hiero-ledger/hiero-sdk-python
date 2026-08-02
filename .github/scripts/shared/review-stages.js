/**
 * Review stage model — single source of truth for PR review lifecycle status
 * and expected-reviewer mapping.
 *
 * All JavaScript scripts that need to reason about "what state is this PR's
 * review in" or "who should be reviewing this" should import from this
 * module instead of re-deriving the logic inline.
 *
 * Environment variable overrides are supported for per-workflow customization:
 *   STAGE_AWAITING_REVIEW, STAGE_CHANGES_REQUESTED, STAGE_APPROVED,
 *   STAGE_AWAITING_TRIAGE
 */

const { GOOD_FIRST_ISSUE_LABEL, BEGINNER_LABEL, INTERMEDIATE_LABEL, ADVANCED_LABEL } = require('./labels');

const AWAITING_REVIEW    = process.env.STAGE_AWAITING_REVIEW?.trim()    || 'awaiting_review';
const CHANGES_REQUESTED  = process.env.STAGE_CHANGES_REQUESTED?.trim()  || 'changes_requested';
const APPROVED           = process.env.STAGE_APPROVED?.trim()           || 'approved';
const AWAITING_TRIAGE    = process.env.STAGE_AWAITING_TRIAGE?.trim()    || 'awaiting_triage';

const REVIEW_STAGES = [
  AWAITING_TRIAGE,
  AWAITING_REVIEW,
  CHANGES_REQUESTED,
  APPROVED,
];

const TRIAGE     = process.env.REVIEWER_TYPE_TRIAGE?.trim()     || 'triage';
const COMMITTER  = process.env.REVIEWER_TYPE_COMMITTER?.trim()  || 'committer';
const MAINTAINER = process.env.REVIEWER_TYPE_MAINTAINER?.trim() || 'maintainer';

function getExpectedReviewers(labels) {
  const labelSet = new Set(Array.isArray(labels) ? labels : []);

  const hasAdvanced     = labelSet.has(ADVANCED_LABEL);
  const hasIntermediate = labelSet.has(INTERMEDIATE_LABEL);
  const hasBeginner     = labelSet.has(BEGINNER_LABEL);
  const hasGfi          = labelSet.has(GOOD_FIRST_ISSUE_LABEL);

  if (hasAdvanced || hasIntermediate) {
    return [COMMITTER, MAINTAINER];
  }

  if (hasBeginner || hasGfi) {
    return [TRIAGE, COMMITTER];
  }

  return [COMMITTER, MAINTAINER];
}

module.exports = {
  AWAITING_REVIEW,
  CHANGES_REQUESTED,
  APPROVED,
  AWAITING_TRIAGE,
  REVIEW_STAGES,
  TRIAGE,
  COMMITTER,
  MAINTAINER,
  getExpectedReviewers,
};
