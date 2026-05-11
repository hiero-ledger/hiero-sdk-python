// SPDX-License-Identifier: Apache-2.0
//
// tests/test-utils.js
//
// Shared test utilities for review-sync test suites.
// Adapted from hiero-sdk-cpp/.github/scripts/tests/test-utils.js
//
// Provides:
//   - runTestSuite()      — CLI-aware test runner with summary
//   - printSummaryAndExit() — formatted results + exit code
//   - createMockGithub()  — mock GitHub API factory with call tracking

// =============================================================================
// SUMMARY & RUNNER
// =============================================================================

/**
 * Prints a summary table and exits with the appropriate code.
 *
 * @param {{ label: string, total: number, passed: number, failed: number }[]} sections
 */
function printSummaryAndExit(sections) {
  console.log('\n' + '='.repeat(70));
  console.log('📈 SUMMARY');
  console.log('='.repeat(70));

  let anyFailed = false;
  for (const { label, total, passed, failed } of sections) {
    if (failed > 0) anyFailed = true;
    console.log(
      `   ${label}: ${total} total, ${passed} passed` +
      `${failed > 0 ? `, ${failed} failed ❌` : ' ✅'}`
    );
  }

  console.log('='.repeat(70));
  process.exit(anyFailed ? 1 : 0);
}

/**
 * Parses the optional test-index CLI argument and either runs a single
 * test or all tests, then prints a summary and exits.
 *
 * @param {string} suiteName - Display name (e.g. "PERMISSIONS TEST SUITE")
 * @param {object[]} scenarios - Array of scenario objects (unused for unit-only suites, pass [])
 * @param {function} runScenario - Async function that runs one scenario (pass async () => true for unit-only)
 * @param {{ label: string, run: () => Promise<{ total: number, passed: number, failed: number }> }[]} extraSections
 */
async function runTestSuite(suiteName, scenarios, runScenario, extraSections = []) {
  console.log(`🧪 ${suiteName}`);
  console.log('='.repeat(suiteName.length + 3) + '\n');

  const summaries = [];

  for (const section of extraSections) {
    const result = await section.run();
    summaries.push({ label: section.label, ...result });
  }

  // Only run integration scenarios if there are any
  if (scenarios.length > 0) {
    console.log('\n\n🔗 INTEGRATION TESTS');
    console.log('='.repeat(70));

    let passed = 0;
    let failed = 0;
    for (let i = 0; i < scenarios.length; i++) {
      const ok = await runScenario(scenarios[i], i);
      if (ok) passed++;
      else failed++;
    }
    summaries.push({ label: 'Integration Tests', total: scenarios.length, passed, failed });
  }

  printSummaryAndExit(summaries);
}

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
      // github.paginate automatically unwraps the array from the response data
      if (result.data && result.data.check_runs) return result.data.check_runs;
      return result.data || result || [];
    },
  };

  return mock;
}

module.exports = { runTestSuite, printSummaryAndExit, createMockGithub };
