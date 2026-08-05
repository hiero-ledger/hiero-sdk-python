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

// ---------------------------------------------------------------------------
// Review stages
// ---------------------------------------------------------------------------

const AWAITING_REVIEW      = process.env.STAGE_AWAITING_REVIEW?.trim()      || 'awaiting_review';
const CHANGES_REQUESTED    = process.env.STAGE_CHANGES_REQUESTED?.trim()    || 'changes_requested';
const APPROVED             = process.env.STAGE_APPROVED?.trim()             || 'approved';
const AWAITING_TRIAGE      = process.env.STAGE_AWAITING_TRIAGE?.trim()      || 'awaiting_triage';
const ROSTER_UNAVAILABLE   = process.env.STAGE_ROSTER_UNAVAILABLE?.trim()   || 'roster_unavailable';

/**
 * All review stages as an array, for validation / iteration.
 */
const REVIEW_STAGES = [
  AWAITING_TRIAGE,
  AWAITING_REVIEW,
  CHANGES_REQUESTED,
  APPROVED,
  ROSTER_UNAVAILABLE,
];

// ---------------------------------------------------------------------------
// Reviewer types
// ---------------------------------------------------------------------------
//
// COMMITTER and MAINTAINER correspond to the CODEOWNERS teams
// @hiero-sdk-python-committers and @hiero-sdk-python-maintainers.
// TRIAGE has no CODEOWNERS-backed GitHub team — it represents community
// triage reviewers who help vet GFI/beginner PRs before a committer picks
// them up.

const TRIAGE     = process.env.REVIEWER_TYPE_TRIAGE?.trim()     || 'triage';
const COMMITTER  = process.env.REVIEWER_TYPE_COMMITTER?.trim()  || 'committer';
const MAINTAINER = process.env.REVIEWER_TYPE_MAINTAINER?.trim() || 'maintainer';

/**
 * Maps a PR's skill/difficulty labels to the reviewer types expected to
 * review it.
 *
 * - Good First Issue / beginner PRs  → triage first, then a committer
 * - Intermediate / advanced PRs      → committer, then a maintainer
 * - No skill label                   → defaults to committer + maintainer
 *   (safest fallback: treat as needing full review rather than under-review)
 * - Multiple skill labels            → the highest difficulty label present
 *   determines the expected reviewers
 *
 * @param {string[]} labels - Label names present on the PR.
 * @returns {string[]} Ordered list of expected reviewer types.
 */
function getExpectedReviewers(labels) {
  const labelSet = new Set(Array.isArray(labels) ? labels : []);

  const hasAdvanced     = labelSet.has(ADVANCED_LABEL);
  const hasIntermediate = labelSet.has(INTERMEDIATE_LABEL);
  const hasBeginner     = labelSet.has(BEGINNER_LABEL);
  const hasGfi          = labelSet.has(GOOD_FIRST_ISSUE_LABEL);

  // Highest difficulty present wins when multiple skill labels are set.
  if (hasAdvanced || hasIntermediate) {
    return [COMMITTER, MAINTAINER];
  }

  if (hasBeginner || hasGfi) {
    return [TRIAGE, COMMITTER];
  }

  // No skill label at all — fall back to the stricter reviewer set.
  return [COMMITTER, MAINTAINER];
}

module.exports = {
  AWAITING_REVIEW,
  CHANGES_REQUESTED,
  APPROVED,
  AWAITING_TRIAGE,
  ROSTER_UNAVAILABLE,
  REVIEW_STAGES,
  TRIAGE,
  COMMITTER,
  MAINTAINER,
  getExpectedReviewers,
};
