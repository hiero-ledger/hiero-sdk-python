
/**
 * Safety floor for the GitHub API rate limit.
 * The workflow will skip processing if remaining calls fall below this.
 */
const RATE_LIMIT_FLOOR = 100;

/**
 * Node ID of the GitHub Projects V2 board.
 * Override via PROJECT_NODE_ID environment variable.
 *
 * Starts with "PVT_" — retrieve via GraphQL as described above.
 */
const PROJECT_NODE_ID = process.env.PROJECT_NODE_ID?.trim() || '';

/**
 * Node ID of the "Priority" Single Select field on the project board.
 * Override via PRIORITY_FIELD_ID environment variable.
 */
const PRIORITY_FIELD_ID = process.env.PRIORITY_FIELD_ID?.trim() || '';

/**
 * Node ID of the "Type" Single Select field on the project board.
 * Override via TYPE_FIELD_ID environment variable.
 */
const TYPE_FIELD_ID = process.env.TYPE_FIELD_ID?.trim() || '';

/**
 * Priority label names — must be applied manually by maintainers to issues.
 * Ordered from most urgent to least urgent (index 0 wins when multiple match).
 */
const PRIORITY_LABELS = [
    {
        name: process.env.PRIORITY_URGENT_LABEL?.trim() || 'priority: urgent',
        color: 'b60205',
        description: 'Drop everything — fix this now',
        optionName: 'Urgent',
    },
    {
        name: process.env.PRIORITY_HIGH_LABEL?.trim() || 'priority: high',
        color: 'e11d48',
        description: 'Should be reviewed in the current cycle',
        optionName: 'High',
    },
    {
        name: process.env.PRIORITY_MEDIUM_LABEL?.trim() || 'priority: medium',
        color: 'f97316',
        description: 'Normal priority — schedule when convenient',
        optionName: 'Medium',
    },
    {
        name: process.env.PRIORITY_LOW_LABEL?.trim() || 'priority: low',
        color: 'fde68a',
        description: 'Nice to have, no urgency',
        optionName: 'Low',
    },
];

/**
 * Type label names — must be applied manually by maintainers to issues.
 * Ordered by precedence (index 0 wins when multiple match).
 */
const TYPE_LABELS = [
    {
        name: process.env.TYPE_BUG_LABEL?.trim() || 'bug',
        color: 'd73a4a',
        description: 'Something is not working',
        optionName: 'Bug',
    },
    {
        name: process.env.TYPE_FEATURE_LABEL?.trim() || 'feature',
        color: 'a2eeef',
        description: 'New feature or enhancement request',
        optionName: 'Feature',
    },
];

/** All managed label objects in one flat array (for ensureLabels). */
const ALL_MANAGED_LABELS = [...PRIORITY_LABELS, ...TYPE_LABELS];

/** All priority label names as a Set for fast membership tests. */
const PRIORITY_LABEL_NAMES = new Set(PRIORITY_LABELS.map((l) => l.name.toLowerCase()));

/** All type label names as a Set for fast membership tests. */
const TYPE_LABEL_NAMES = new Set(TYPE_LABELS.map((l) => l.name.toLowerCase()));

module.exports = {
    RATE_LIMIT_FLOOR,
    PROJECT_NODE_ID,
    PRIORITY_FIELD_ID,
    TYPE_FIELD_ID,
    PRIORITY_LABELS,
    TYPE_LABELS,
    ALL_MANAGED_LABELS,
    PRIORITY_LABEL_NAMES,
    TYPE_LABEL_NAMES,
};
