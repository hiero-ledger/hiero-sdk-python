// ---------------------------------------------------------------------------
// Spam helpers
// ---------------------------------------------------------------------------

const fs = require("fs");
const { CONFIG, LEVEL_KEYS } = require("../config");
const REDUCED_LIMIT_LEVELS = new Set([LEVEL_KEYS.GFI, LEVEL_KEYS.INTERMEDIATE]);

/**
 * Returns true if the contributor appears in the spam list.
 *
 * The spam list is maintained as one username per line.
 * Blank lines and comments beginning with "#" are ignored.
 *
 * @param {string} username
 * @returns {boolean}
 */
function isSpamUser(username) {
    if (!fs.existsSync(CONFIG.spamListPath)) {
        return false;
    }
    const users = fs
        .readFileSync(CONFIG.spamListPath, "utf8")
        .split("\n")
        .map(line => line.trim())
        .filter(line => line && !line.startsWith("#"))
        .map(line => line.toLowerCase());
    return users.includes(username.toLowerCase());
}

/**
 * Returns true if spam-listed users are completely blocked
 * from requesting assignments at this difficulty.
 *
 * @param {string} levelKey
 * @returns {boolean}
 */
function spamUsersBlocked(levelKey) {
    return (
        levelKey === LEVEL_KEYS.BEGINNER ||
        levelKey === LEVEL_KEYS.ADVANCED
    );
}

/**
 * Returns the effective assignment limit for a contributor.
 *
 * Spam-listed contributors may receive a stricter limit than
 * the normal limit configured for the skill level.
 *
 * @param {string} levelKey
 * @param {boolean} spamUser
 * @returns {number}
 */
function getAssignmentLimit(levelKey, spamUser) {
    const defaultLimit =
        levelKey === LEVEL_KEYS.ADVANCED ? 1 : 2;

    if (!spamUser) {
        return defaultLimit;
    }

    if (REDUCED_LIMIT_LEVELS.has(levelKey)) {
        return 1;
    }

    return defaultLimit;
}

function isSpamLimited(levelKey, spamUser) {
    return spamUser && REDUCED_LIMIT_LEVELS.has(levelKey);
}

module.exports = {
  isSpamUser,
  spamUsersBlocked,
  getAssignmentLimit,
  isSpamLimited,
};
