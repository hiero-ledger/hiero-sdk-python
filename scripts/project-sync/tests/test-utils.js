
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
 * @param {string}    suiteName   - Display name (e.g. "MAPPING TEST SUITE")
 * @param {object[]}  scenarios   - Integration scenario array (pass [] for unit-only suites)
 * @param {function}  runScenario - Async function that runs one scenario
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


/**
 * Creates a mock GitHub API object for project-sync tests.
 * Tracks GraphQL calls, label operations, and issue fetches via the returned
 * calls object.
 *
 * @param {object} options
 * @param {Record<string, boolean>}  options.existingLabels
 *   Map of label name → true (label already exists in the repo)
 * @param {object[]} options.graphqlResponses
 *   Array of objects returned by successive graphql() calls (in order)
 * @param {Record<number, object>}   options.issues
 *   Map of issue number → issue data returned by issues.get
 * @returns {{ calls: object, rest: object, graphql: function }}
 */
function createMockGithub(options = {}) {
    const {
        existingLabels = {},
        graphqlResponses = [],
        issues = {},
    } = options;

    let graphqlCallIndex = 0;

    const calls = {
        labelsCreated: [],
        labelsChecked: [],
        graphqlCalls: [],   // { query, variables } for each call
        issuesFetched: [],
    };

    const mock = {
        calls,
        rest: {
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
                get: async ({ issue_number }) => {
                    calls.issuesFetched.push(issue_number);
                    const issue = issues[issue_number];
                    if (!issue) {
                        throw Object.assign(new Error('Not found'), { status: 404 });
                    }
                    return { data: issue };
                },
            },
        },
        graphql: async (query, variables) => {
            calls.graphqlCalls.push({ query: query.trim(), variables });
            const response = graphqlResponses[graphqlCallIndex];
            graphqlCallIndex++;
            if (response === undefined) {
                throw new Error(
                    `Unexpected graphql call #${graphqlCallIndex}: no response stub provided.`
                );
            }
            if (response instanceof Error) throw response;
            return response;
        },
    };

    return mock;
}

module.exports = { runTestSuite, printSummaryAndExit, createMockGithub };
