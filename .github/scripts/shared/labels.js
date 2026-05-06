/**
 * Centralized label configuration — single source of truth for difficulty labels.
 *
 * All JavaScript scripts that reference difficulty labels should import
 * constants from this module instead of hardcoding strings.
 *
 * To rename labels in the future, update the defaults below and the
 * corresponding workflow YAML `if:` conditions (which cannot import JS).
 *
 * Environment variable overrides are supported for per-workflow customization:
 *   GOOD_FIRST_ISSUE_LABEL, GOOD_FIRST_ISSUE_CANDIDATE_LABEL,
 *   BEGINNER_LABEL, INTERMEDIATE_LABEL, ADVANCED_LABEL
 */

const GOOD_FIRST_ISSUE_LABEL           = process.env.GOOD_FIRST_ISSUE_LABEL?.trim()           || 'Good First Issue';
const GOOD_FIRST_ISSUE_CANDIDATE_LABEL = process.env.GOOD_FIRST_ISSUE_CANDIDATE_LABEL?.trim() || 'Good First Issue Candidate';
const BEGINNER_LABEL                   = process.env.BEGINNER_LABEL?.trim()                   || 'skill: beginner';
const INTERMEDIATE_LABEL               = process.env.INTERMEDIATE_LABEL?.trim()               || 'skill: intermediate';
const ADVANCED_LABEL                   = process.env.ADVANCED_LABEL?.trim()                   || 'skill: advanced';

/**
 * All difficulty labels as an array, ordered by ascending difficulty.
 *
 * Scripts that need to check whether an issue has *any* difficulty label
 * (e.g. coderabbit_plan_trigger) should test against this array.
 */
const DIFFICULTY_LABELS = [
  GOOD_FIRST_ISSUE_LABEL,
  BEGINNER_LABEL,
  INTERMEDIATE_LABEL,
  ADVANCED_LABEL,
];

/**
 * Validates a label string for safe use in API queries.
 *
 * Allows letters, digits, and the characters: . _ / : space -
 * This is intentionally looser than `isSafeSearchToken` (which rejects
 * colons and spaces) because labels like "skill: beginner" are valid.
 *
 * The hyphen is escaped (\-) to prevent accidental ASCII range creation
 * if a future developer appends characters to the character class.
 *
 * @param {string} value - The label string to validate.
 * @returns {boolean} True if the value is safe for use in queries.
 */
function isSafeLabel(value) {
  return typeof value === 'string' && value.trim().length > 0 && /^[a-zA-Z0-9._/: \-]+$/.test(value);
}

module.exports = {
  GOOD_FIRST_ISSUE_LABEL,
  GOOD_FIRST_ISSUE_CANDIDATE_LABEL,
  BEGINNER_LABEL,
  INTERMEDIATE_LABEL,
  ADVANCED_LABEL,
  DIFFICULTY_LABELS,
  isSafeLabel,
};
