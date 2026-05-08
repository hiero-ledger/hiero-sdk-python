// SPDX-License-Identifier: Apache-2.0
//
// helpers/index.js
//
// Namespaced barrel export for review-sync helpers.
// Uses namespacing to prevent silent name collisions from spread exports.
//
// Usage:
//   const helpers = require('./helpers');
//   const { QUEUE_LABELS } = helpers.constants;
//   const { syncLabel } = helpers.labels;

module.exports = {
  constants: require('./constants'),
  permissions: require('./permissions'),
  reviews: require('./reviews'),
  labels: require('./labels'),
  status: require('./status'),
};
