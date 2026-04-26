// SPDX-License-Identifier: Apache-2.0

/**
 * @fileoverview
 * Simple logger utility for GitHub Actions bots with consistent
 * prefixes and levels.
 */

/**
 * Creates a logger instance for a specific bot.
 *
 * @param {string} botName - Name of the bot (e.g. 'reviewers-assignee')
 * @returns {{
 *   log:   (...args: any[]) => void,
 *   info:  (...args: any[]) => void,
 *   warn:  (...args: any[]) => void,
 *   error: (...args: any[]) => void
 * }} Logger with consistent prefix
 */
function createLogger(botName) {
  const prefix = `[${botName}]`;
  return {
    log:   (...args) => console.log(prefix, ...args),
    info:  (...args) => console.info(prefix, ...args),
    warn:  (...args) => console.warn(prefix, ...args),
    error: (...args) => console.error(prefix, ...args),
  };
}

module.exports = { createLogger };
