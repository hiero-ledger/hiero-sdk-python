// SPDX-License-Identifier: Apache-2.0
//
// helpers/constants.js
//
// Shared constants for the Review Queue Label Sync.

/**
 * Safety floor for the GitHub API rate limit.
 * The cron job will skip processing if remaining calls fall below this.
 */
const RATE_LIMIT_FLOOR = 200;

/**
 * The four mutually exclusive queue labels managed by this bot.
 *
 * Flow:
 *   queue:junior-committer → queue:committers → queue:maintainers → ready-to-merge
 */
const QUEUE_LABELS = {
  JUNIOR: {
    name: 'queue:junior-committer',
    color: 'e4e669',
    description: 'PR awaiting initial quality review',
  },
  COMMITTERS: {
    name: 'queue:committers',
    color: '0075ca',
    description: 'PR awaiting committer technical review',
  },
  MAINTAINERS: {
    name: 'queue:maintainers',
    color: 'd876e3',
    description: 'PR awaiting maintainer final review',
  },
  MERGE: {
    name: 'ready-to-merge',
    color: '0e8a16',
    description: 'PR approved by maintainer and ready to merge',
  },
};

/** All queue label names, used for cleanup operations. */
const ALL_QUEUE_LABEL_NAMES = Object.values(QUEUE_LABELS).map((l) => l.name);

module.exports = { RATE_LIMIT_FLOOR, QUEUE_LABELS, ALL_QUEUE_LABEL_NAMES };
