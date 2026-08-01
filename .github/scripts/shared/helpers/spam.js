// ---------------------------------------------------------------------------
// Spam helpers
// ---------------------------------------------------------------------------

const fs = require("fs");
const { CONFIG, LEVEL_KEYS } = require("../config");

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
    if (!fs.existsSync(CONFIG.spamPolicy.spamListPath)) {
        return false;
    }
    const users = fs
        .readFileSync(CONFIG.spamPolicy.spamListPath, "utf8")
        .split("\n")
        .map(line => line.trim())
        .filter(line => line && !line.startsWith("#"))
        .map(line => line.toLowerCase());
    return users.includes(username.toLowerCase());
}

/**
 * Returns true if spam-listed users are completely blocked
 * from requesting assignments at the given level.
 *
 * @param {string} levelKey
 * @returns {boolean}
 */
function spamUsersBlocked(levelKey) {
    return !CONFIG.spamPolicy.allowedLevels.includes(levelKey);
}

/**
 * Returns the effective assignment limit for a contributor.
 *
 * Spam-listed contributors receive the configured spam limit,
 * while normal contributors use the standard limits.
 *
 * @param {string} levelKey
 * @param {boolean} spamUser
 * @returns {number}
 */
function getAssignmentLimit(levelKey, spamUser) {
    if (spamUser) {
        return CONFIG.spamPolicy.assignmentLimit;
    }
    return levelKey === "advanced" ? 1 : 2;
}
a
/**

 * Returns true when a spam-listed contributor is subject
 * to a reduced assignment limit.
 *
 * @param {string} levelKey
 * @param {boolean} spamUser
 * @returns {boolean}
 */
function isSpamLimited(levelKey, spamUser) {
    return (
        spamUser &&
        getAssignmentLimit(levelKey, true) <
        getAssignmentLimit(levelKey, false)
    );
}

module.exports = {
  isSpamUser,
  spamUsersBlocked,
  getAssignmentLimit,
  isSpamLimited,
};
