// SPDX-License-Identifier: Apache-2.0
//
// helpers/constants.js
//
// Shared constants for bot scripts: maintainer team, labels, issue state.

const { loadAutomationConfig, buildConstants } = require('./config-loader');

/**
 * Parsed and validated automation config loaded from .github/hiero-automation.json.
 * Exposed for modules that need access to nested config values (e.g. assignment limits).
 */
const AUTOMATION_CONFIG = loadAutomationConfig();

/**
 * Derived constants built from the automation config. Preserves the flat
 * constant shapes (MAINTAINER_TEAM, LABELS, SKILL_HIERARCHY, etc.) that
 * the rest of the bot scripts expect.
 */
const derived = buildConstants(AUTOMATION_CONFIG);

/**
 * Team to tag when manual intervention is needed.
 */
const MAINTAINER_TEAM = derived.MAINTAINER_TEAM;

/**
 * Team to tag in Good First Issue welcome comments.
 */
const GFI_SUPPORT_TEAM = derived.GFI_SUPPORT_TEAM;

/**
 * Common label constants used across bot scripts.
 */
const LABELS = derived.LABELS;

/**
 * Skill hierarchy used to determine progression for recommendations.
 */
const SKILL_HIERARCHY = derived.SKILL_HIERARCHY;

/**
 * Priority hierarchy for issue recommendations.
 */
const PRIORITY_HIERARCHY = derived.PRIORITY_HIERARCHY;

/**
 * Issue state values for GitHub search queries.
 */
const ISSUE_STATE = Object.freeze({
  OPEN: 'open',
  CLOSED: 'closed',
});

/**
 * Skill-level prerequisite map. Each key is a LABELS skill-level constant.
 * - requiredLabel: the prerequisite skill label the user must have completed, or null if none.
 * - requiredCount: how many closed issues with requiredLabel the user needs.
 * - displayName: human-readable name for the current skill level.
 * - prerequisiteDisplayName: human-readable plural name for the prerequisite level (used in comments).
 *
 * Progression: Good First Issue (no prereqs) -> Beginner (2 GFI) -> Intermediate (3 Beginner) -> Advanced (3 Intermediate).
 * @type {Object<string, { requiredLabel: string|null, requiredCount: number, displayName: string, prerequisiteDisplayName?: string }>}
 */
const SKILL_PREREQUISITES = derived.SKILL_PREREQUISITES;

/**
 * Documentation links loaded from the automation config.
 * @type {{ workflowGuide: string, readme: string, signingGuide: string, mergeConflictsGuide: string }}
 */
const DOCUMENTATION = derived.DOCUMENTATION;

/**
 * Community links loaded from the automation config.
 * @type {{ discordChannel: string }}
 */
const COMMUNITY = derived.COMMUNITY;

module.exports = {
  MAINTAINER_TEAM,
  GFI_SUPPORT_TEAM,
  LABELS,
  ISSUE_STATE,
  SKILL_HIERARCHY,
  SKILL_PREREQUISITES,
  PRIORITY_HIERARCHY,
  DOCUMENTATION,
  COMMUNITY,
  AUTOMATION_CONFIG,
};
