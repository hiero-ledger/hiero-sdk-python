// SPDX-License-Identifier: Apache-2.0
//
// __tests__/test-utils.js
//
// Shared Jest test utilities .
//
// Provides:
//   - createMockGithub()  — mock GitHub API factory with call tracking

// =============================================================================
// MOCK GITHUB FACTORY
// =============================================================================

/**
 * Creates a mock GitHub API object for review-sync tests.
 * Tracks labels, permission checks, and review fetches via the returned calls object.
 *
 * @param {object} options
 * @param {Record<string, { role_name?: string, permission?: string }>} options.roles
 *   Map of username → permission data returned by getCollaboratorPermissionLevel
 * @param {Array} options.reviews
 *   Array of review objects returned by pulls.listReviews
 * @param {Record<string, boolean>} options.existingLabels
 *   Map of label name → true (label exists in repo)
 * @returns {{ calls: object, rest: object, paginate: function }}
 */
function createMockGithub(options = {}) {
  const {
    roles = {},
    reviews = [],
    existingLabels = {},
    checkRuns = [],
  } = options;

  const calls = {
    labelsAdded: [],
    labelsRemoved: [],
    labelsCreated: [],
    labelsChecked: [],
    permissionsChecked: [],
  };

  const mock = {
    calls,
    rest: {
      repos: {
        getCollaboratorPermissionLevel: async ({ username }) => {
          calls.permissionsChecked.push(username);
          const role = roles[username];
          if (!role) {
            throw Object.assign(new Error('Not found'), { status: 404 });
          }
          return { data: role };
        },
      },
      pulls: {
        listReviews: async () => ({ data: reviews }),
      },
      checks: {
        listForRef: async () => ({ data: { check_runs: checkRuns } }),
      },
      issues: {
        getLabel: async ({ name }) => {
          calls.labelsChecked.push(name);
          if (!existingLabels[name]) {
            throw Object.assign(new Error('Not found'), { status: 404 });
          }
          return { data: { name } };
        },
        createLabel: async ({ name, color, description }) => {
          calls.labelsCreated.push({ name, color, description });
          return {};
        },
        addLabels: async ({ labels }) => {
          calls.labelsAdded.push(...labels);
          return {};
        },
        removeLabel: async ({ name }) => {
          calls.labelsRemoved.push(name);
          return {};
        },
      },
      rateLimit: {
        get: async () => ({
          data: { resources: { core: { remaining: 5000 } } },
        }),
      },
    },
    paginate: async (fn, opts) => {
      const result = await fn(opts);
      if (result.data && result.data.check_runs) return result.data.check_runs;
      return result.data || result || [];
    },
  };

  return mock;
}

module.exports = { createMockGithub };
