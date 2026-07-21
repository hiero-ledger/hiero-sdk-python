// SPDX-License-Identifier: Apache-2.0
//
// helpers/config-loader.js
//
// Loads and validates the repository automation configuration from
// .github/hiero-automation.json. Provides buildConstants() to map
// the nested config structure back into the flat constant shapes
// consumed by the rest of the bot scripts.

const fs = require('fs');

const path = require('path');

/**
 * Default path to the repository automation config file.
 * Resolves from helpers/ → scripts/ → .github/hiero-automation.json.
 * @type {string}
 */
const DEFAULT_CONFIG_PATH = path.resolve(__dirname, '../../hiero-automation.json');

/**
 * Validates that a value is a non-empty string.
 * @param {*} value
 * @returns {boolean}
 */
function isNonEmptyString(value) {
  return typeof value === 'string' && value.trim().length > 0;
}

/**
 * Validates that a value is a positive integer (> 0).
 * @param {*} value
 * @returns {boolean}
 */
function isPositiveInteger(value) {
  return Number.isInteger(value) && value > 0;
}

/**
 * Required keys for each label group, documentation, and community.
 * If a key is missing from the config, buildConstants() would produce
 * undefined — so we fail early with a clear message.
 */
const REQUIRED_STATUS_KEYS = ['awaitingTriage', 'readyForDev', 'inProgress', 'blocked', 'needsReview', 'needsRevision'];
const REQUIRED_SKILL_KEYS = ['goodFirstIssue', 'beginner', 'intermediate', 'advanced'];
const REQUIRED_PRIORITY_KEYS = ['critical', 'high', 'medium', 'low'];
const REQUIRED_DOC_KEYS = ['workflowGuide', 'readme', 'signingGuide', 'mergeConflictsGuide'];
const REQUIRED_COMMUNITY_KEYS = ['discordChannel'];

/**
 * Validates that team references are non-empty strings.
 * @param {object} config - The parsed config object.
 * @param {string[]} errors - Mutable array to push error messages into.
 */
function validateTeams(config, errors) {
  if (!isNonEmptyString(config.maintainerTeam)) {
    errors.push('maintainerTeam must be a non-empty string');
  }
  if (!isNonEmptyString(config.goodFirstIssueSupportTeam)) {
    errors.push('goodFirstIssueSupportTeam must be a non-empty string');
  }
}

/**
 * Validates that labels.status, labels.skill, and labels.priority each exist
 * as objects containing all required keys with non-empty string values.
 * @param {object} config - The parsed config object.
 * @param {string[]} errors - Mutable array to push error messages into.
 */
function validateLabels(config, errors) {
  if (!config.labels || typeof config.labels !== 'object') {
    errors.push('labels must be an object');
    return;
  }
  const requiredKeysMap = {
    status: REQUIRED_STATUS_KEYS,
    skill: REQUIRED_SKILL_KEYS,
    priority: REQUIRED_PRIORITY_KEYS,
  };
  for (const [group, requiredKeys] of Object.entries(requiredKeysMap)) {
    if (!config.labels[group] || typeof config.labels[group] !== 'object') {
      errors.push(`labels.${group} must be an object`);
    } else {
      for (const key of requiredKeys) {
        if (!isNonEmptyString(config.labels[group][key])) {
          errors.push(`labels.${group}.${key} is required and must be a non-empty string`);
        }
      }
    }
  }
}

/**
 * Validates a single hierarchy array: non-empty, unique entries,
 * and all values exist in the corresponding label group.
 * @param {object} config - The parsed config object.
 * @param {string[]} errors - Mutable array to push error messages into.
 * @param {string} hierarchyKey - 'skillHierarchy' or 'priorityHierarchy'.
 * @param {string} labelGroup - 'skill' or 'priority' (key in config.labels).
 */
function validateSingleHierarchy(config, errors, hierarchyKey, labelGroup) {
  const hierarchy = config[hierarchyKey];

  if (!Array.isArray(hierarchy) || hierarchy.length === 0) {
    errors.push(`${hierarchyKey} must be a non-empty array`);
    return;
  }

  const seen = new Set();
  for (const entry of hierarchy) {
    if (seen.has(entry)) {
      errors.push(`${hierarchyKey} entry "${entry}" appears more than once`);
    }
    seen.add(entry);
  }

  if (config.labels && config.labels[labelGroup]) {
    const labelValues = Object.values(config.labels[labelGroup]);
    for (const entry of hierarchy) {
      if (!labelValues.includes(entry)) {
        errors.push(`${hierarchyKey} entry "${entry}" not found in labels.${labelGroup} values`);
      }
    }
  }
}

/**
 * Validates that skillHierarchy and priorityHierarchy are non-empty arrays
 * whose entries are unique and exist in the corresponding label group values.
 * @param {object} config - The parsed config object.
 * @param {string[]} errors - Mutable array to push error messages into.
 */
function validateHierarchies(config, errors) {
  validateSingleHierarchy(config, errors, 'skillHierarchy', 'skill');
  validateSingleHierarchy(config, errors, 'priorityHierarchy', 'priority');
}

/**
 * Validates a single prerequisite object shape: requiredLabel, requiredCount,
 * displayName, and prerequisiteDisplayName (when requiredLabel is not null).
 * @param {string} key - The skillPrerequisites key being validated.
 * @param {object} prereq - The prerequisite object.
 * @param {string[]} hierarchy - The skillHierarchy array for cross-reference.
 * @param {string[]} errors - Mutable array to push error messages into.
 */
function validatePrerequisiteShape(key, prereq, hierarchy, errors) {
  if (!prereq || typeof prereq !== 'object') {
    errors.push(`skillPrerequisites["${key}"] must be an object`);
    return;
  }
  if (!('requiredLabel' in prereq)) {
    errors.push(`skillPrerequisites["${key}"].requiredLabel is required (use null for no prerequisite)`);
  }
  if (!Number.isInteger(prereq.requiredCount) || prereq.requiredCount < 0) {
    errors.push(`skillPrerequisites["${key}"].requiredCount must be a non-negative integer`);
  }
  if (!isNonEmptyString(prereq.displayName)) {
    errors.push(`skillPrerequisites["${key}"].displayName is required and must be a non-empty string`);
  }
  if (prereq.requiredLabel !== null && !isNonEmptyString(prereq.prerequisiteDisplayName)) {
    errors.push(`skillPrerequisites["${key}"].prerequisiteDisplayName is required when requiredLabel is not null`);
  }
  if (prereq.requiredLabel !== null && prereq.requiredLabel !== undefined && !hierarchy.includes(prereq.requiredLabel)) {
    errors.push(`skillPrerequisites["${key}"].requiredLabel "${prereq.requiredLabel}" not found in skillHierarchy`);
  }
}

/**
 * Validates skillPrerequisites: coverage (every hierarchy entry has a
 * prerequisites entry), membership (every key is in the hierarchy), and
 * individual prerequisite object shape.
 * @param {object} config - The parsed config object.
 * @param {string[]} errors - Mutable array to push error messages into.
 */
function validateSkillPrerequisites(config, errors) {
  if (!config.skillPrerequisites || typeof config.skillPrerequisites !== 'object') {
    errors.push('skillPrerequisites must be an object');
    return;
  }
  if (!Array.isArray(config.skillHierarchy)) return;

  for (const skill of config.skillHierarchy) {
    if (!config.skillPrerequisites[skill]) {
      errors.push(`skillPrerequisites is missing entry for skillHierarchy value "${skill}"`);
    }
  }
  for (const [key, prereq] of Object.entries(config.skillPrerequisites)) {
    if (!config.skillHierarchy.includes(key)) {
      errors.push(`skillPrerequisites key "${key}" not found in skillHierarchy`);
    }
    validatePrerequisiteShape(key, prereq, config.skillHierarchy, errors);
  }
}

/**
 * Validates that assignmentLimits contains positive integer values for
 * maxOpenAssignments and maxGfiCompletions.
 * @param {object} config - The parsed config object.
 * @param {string[]} errors - Mutable array to push error messages into.
 */
function validateAssignmentLimits(config, errors) {
  if (!config.assignmentLimits || typeof config.assignmentLimits !== 'object') {
    errors.push('assignmentLimits must be an object');
    return;
  }
  if (!isPositiveInteger(config.assignmentLimits.maxOpenAssignments)) {
    errors.push('assignmentLimits.maxOpenAssignments must be a positive integer');
  }
  if (!isPositiveInteger(config.assignmentLimits.maxGfiCompletions)) {
    errors.push('assignmentLimits.maxGfiCompletions must be a positive integer');
  }
}

/**
 * Validates that a config section exists as an object and contains all
 * required keys as non-empty strings.
 * @param {object} config - The parsed config object.
 * @param {string} section - The top-level config key (e.g. 'documentation').
 * @param {string[]} requiredKeys - Keys that must be present with non-empty string values.
 * @param {string[]} errors - Mutable array to push error messages into.
 */
function validateRequiredKeys(config, section, requiredKeys, errors) {
  if (!config[section] || typeof config[section] !== 'object') {
    errors.push(`${section} must be an object`);
    return;
  }
  for (const key of requiredKeys) {
    if (!isNonEmptyString(config[section][key])) {
      errors.push(`${section}.${key} is required and must be a non-empty string`);
    }
  }
}

/**
 * Validates the parsed automation config object. Collects all violations
 * and throws a single error listing every problem found.
 *
 * Checks:
 *   - teams are non-empty strings
 *   - labels.status, labels.skill, labels.priority exist with all required keys as non-empty strings
 *   - every skillHierarchy entry exists in labels.skill values
 *   - every priorityHierarchy entry exists in labels.priority values
 *   - every skillHierarchy entry has a corresponding skillPrerequisites entry
 *   - every skillPrerequisites key exists in skillHierarchy
 *   - every prerequisite object has requiredLabel, requiredCount, displayName
 *   - prerequisiteDisplayName is required when requiredLabel is not null
 *   - every non-null requiredLabel exists in skillHierarchy
 *   - assignment limits are positive integers
 *   - documentation has all required keys as non-empty strings
 *   - community has all required keys as non-empty strings
 *
 * @param {object} config - The parsed config object.
 * @throws {Error} If any validation rule is violated.
 */
function validateConfig(config) {
  const errors = [];

  validateTeams(config, errors);
  validateLabels(config, errors);
  validateHierarchies(config, errors);
  validateSkillPrerequisites(config, errors);
  validateAssignmentLimits(config, errors);
  validateRequiredKeys(config, 'documentation', REQUIRED_DOC_KEYS, errors);
  validateRequiredKeys(config, 'community', REQUIRED_COMMUNITY_KEYS, errors);

  if (errors.length > 0) {
    throw new Error(
      `Invalid hiero-automation.json:\n${errors.map((e) => `  - ${e}`).join('\n')}`,
    );
  }
}

/**
 * Reads, parses, and validates the repository automation config file.
 *
 * @param {string} [configPath=DEFAULT_CONFIG_PATH] - Absolute path to the JSON config file.
 * @returns {object} The validated, frozen config object.
 * @throws {Error} If the file cannot be read, parsed, or fails validation.
 */
function loadAutomationConfig(configPath = DEFAULT_CONFIG_PATH) {
  let raw;
  try {
    raw = fs.readFileSync(configPath, 'utf8');
  } catch (err) {
    throw new Error(
      `Failed to read automation config at ${configPath}: ${err.message}`,
    );
  }

  let config;
  try {
    config = JSON.parse(raw);
  } catch (err) {
    throw new Error(
      `Failed to parse automation config at ${configPath}: ${err.message}`,
    );
  }

  validateConfig(config);
  return Object.freeze(config);
}

/**
 * Maps the nested config structure back into the flat constant shapes
 * consumed by the rest of the bot scripts. The returned object contains
 * every derived constant that was previously hardcoded in constants.js,
 * assign-comments.js, finalize-comments.js, and comments.js.
 *
 * @param {object} config - A validated config object from loadAutomationConfig.
 * @returns {{
 *   MAINTAINER_TEAM: string,
 *   GFI_SUPPORT_TEAM: string,
 *   LABELS: object,
 *   SKILL_HIERARCHY: string[],
 *   PRIORITY_HIERARCHY: string[],
 *   SKILL_PREREQUISITES: object,
 *   DOCUMENTATION: object,
 *   COMMUNITY: object,
 * }}
 */
function buildConstants(config) {
  const LABELS = Object.freeze({
    // Status labels
    AWAITING_TRIAGE: config.labels.status.awaitingTriage,
    READY_FOR_DEV: config.labels.status.readyForDev,
    IN_PROGRESS: config.labels.status.inProgress,
    BLOCKED: config.labels.status.blocked,
    NEEDS_REVIEW: config.labels.status.needsReview,
    NEEDS_REVISION: config.labels.status.needsRevision,

    // Skill level labels
    GOOD_FIRST_ISSUE: config.labels.skill.goodFirstIssue,
    BEGINNER: config.labels.skill.beginner,
    INTERMEDIATE: config.labels.skill.intermediate,
    ADVANCED: config.labels.skill.advanced,

    // Priority labels
    PRIORITY_CRITICAL: config.labels.priority.critical,
    PRIORITY_HIGH: config.labels.priority.high,
    PRIORITY_MEDIUM: config.labels.priority.medium,
    PRIORITY_LOW: config.labels.priority.low,
  });

  const SKILL_HIERARCHY = Object.freeze([...config.skillHierarchy]);
  const PRIORITY_HIERARCHY = Object.freeze([...config.priorityHierarchy]);

  const SKILL_PREREQUISITES = {};
  for (const [key, value] of Object.entries(config.skillPrerequisites)) {
    SKILL_PREREQUISITES[key] = Object.freeze({ ...value });
  }
  Object.freeze(SKILL_PREREQUISITES);

  return {
    MAINTAINER_TEAM: config.maintainerTeam,
    GFI_SUPPORT_TEAM: config.goodFirstIssueSupportTeam,
    LABELS,
    SKILL_HIERARCHY,
    PRIORITY_HIERARCHY,
    SKILL_PREREQUISITES,
    DOCUMENTATION: Object.freeze({ ...config.documentation }),
    COMMUNITY: Object.freeze({ ...config.community }),
  };
}

module.exports = {
  DEFAULT_CONFIG_PATH,
  loadAutomationConfig,
  buildConstants,
};
