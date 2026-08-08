const { PRIORITY_LABELS, TYPE_LABELS } = require('./constants');

/**
 * Derive the Priority and Type option names from a list of label names.
 *
 * The returned values (e.g. "Urgent", "Bug") are the human-readable option
 * names configured on the project board, not node IDs.  The caller is
 * responsible for resolving them to option IDs via fetchProjectFields().
 *
 * @param {string[]} labelNames - Labels currently on the linked issue
 * @returns {{ priority: string|null, type: string|null }}
 *   priority: the option name to set on the Priority field, or null
 *   type:     the option name to set on the Type field, or null
 */
function deriveFieldValues(labelNames) {
    const lower = new Set(labelNames.map((l) => l.toLowerCase()));

    // Pick the highest-priority label present (lowest index wins)
    let priority = null;
    for (const label of PRIORITY_LABELS) {
        if (lower.has(label.name.toLowerCase())) {
            priority = label.optionName;
            break;
        }
    }

    // Pick the first matching type label (bug > feature)
    let type = null;
    for (const label of TYPE_LABELS) {
        if (lower.has(label.name.toLowerCase())) {
            type = label.optionName;
            break;
        }
    }

    return { priority, type };
}

module.exports = { deriveFieldValues };
