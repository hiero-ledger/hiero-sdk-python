// SPDX-License-Identifier: Apache-2.0
//
// tests/test-linked-issues.js
//
// Unit tests for helpers/linked-issues.js (getLinkedIssueLabels).
// Run with: node .github/scripts/project-sync/tests/test-linked-issues.js

const { runTestSuite, createMockGithub } = require('./test-utils');
const { getLinkedIssueLabels } = require('../helpers/linked-issues');

const unitTests = [
    {
        name: 'getLinkedIssueLabels: empty body → []',
        test: async () => {
            const mock = createMockGithub({ issues: {} });
            const labels = await getLinkedIssueLabels('', mock, 'o', 'r');
            return labels.length === 0 && mock.calls.issuesFetched.length === 0;
        },
    },
    {
        name: 'getLinkedIssueLabels: null body → []',
        test: async () => {
            const mock = createMockGithub({ issues: {} });
            const labels = await getLinkedIssueLabels(null, mock, 'o', 'r');
            return labels.length === 0;
        },
    },
    {
        name: 'getLinkedIssueLabels: no closing keywords → []',
        test: async () => {
            const mock = createMockGithub({ issues: {} });
            const labels = await getLinkedIssueLabels('See also #42 and #99', mock, 'o', 'r');
            return labels.length === 0;
        },
    },
    {
        name: 'getLinkedIssueLabels: "closes #1" extracts priority label',
        test: async () => {
            const mock = createMockGithub({
                issues: { 1: { labels: [{ name: 'priority: high' }] } },
            });
            const labels = await getLinkedIssueLabels('closes #1', mock, 'o', 'r');
            return labels.includes('priority: high');
        },
    },
    {
        name: 'getLinkedIssueLabels: "fixes #2" extracts type label',
        test: async () => {
            const mock = createMockGithub({
                issues: { 2: { labels: [{ name: 'bug' }] } },
            });
            const labels = await getLinkedIssueLabels('fixes #2', mock, 'o', 'r');
            return labels.includes('bug');
        },
    },
    {
        name: 'getLinkedIssueLabels: "resolves #3" is recognised',
        test: async () => {
            const mock = createMockGithub({
                issues: { 3: { labels: [{ name: 'priority: urgent' }] } },
            });
            const labels = await getLinkedIssueLabels('resolves #3', mock, 'o', 'r');
            return labels.includes('priority: urgent');
        },
    },
    {
        name: 'getLinkedIssueLabels: filters out non-priority non-type labels',
        test: async () => {
            const mock = createMockGithub({
                issues: {
                    5: { labels: [{ name: 'skill: beginner' }, { name: 'help wanted' }, { name: 'bug' }] },
                },
            });
            const labels = await getLinkedIssueLabels('closes #5', mock, 'o', 'r');
            return labels.length === 1 && labels[0] === 'bug';
        },
    },
    {
        name: 'getLinkedIssueLabels: deduplicates across multiple linked issues',
        test: async () => {
            const mock = createMockGithub({
                issues: {
                    10: { labels: [{ name: 'priority: high' }, { name: 'bug' }] },
                    11: { labels: [{ name: 'priority: high' }, { name: 'feature' }] },
                },
            });
            const labels = await getLinkedIssueLabels('closes #10\nfixes #11', mock, 'o', 'r');
            // 'priority: high' appears in both — should be deduplicated
            const priorityCount = labels.filter((l) => l === 'priority: high').length;
            return priorityCount === 1 && labels.includes('bug') && labels.includes('feature');
        },
    },
    {
        name: 'getLinkedIssueLabels: skips linked PRs (issue.pull_request truthy)',
        test: async () => {
            const mock = createMockGithub({
                issues: {
                    7: { pull_request: {}, labels: [{ name: 'bug' }] },
                },
            });
            const labels = await getLinkedIssueLabels('closes #7', mock, 'o', 'r');
            return labels.length === 0;
        },
    },
    {
        name: 'getLinkedIssueLabels: 404 on one issue does not abort the rest',
        test: async () => {
            const mock = createMockGithub({
                issues: {
                    // issue 20 does not exist (will 404)
                    21: { labels: [{ name: 'priority: medium' }] },
                },
            });
            const labels = await getLinkedIssueLabels('closes #20\ncloses #21', mock, 'o', 'r');
            return labels.includes('priority: medium');
        },
    },
    {
        name: 'getLinkedIssueLabels: string labels (not objects) are handled',
        test: async () => {
            const mock = createMockGithub({
                issues: { 30: { labels: ['bug', 'priority: low'] } },
            });
            const labels = await getLinkedIssueLabels('closes #30', mock, 'o', 'r');
            return labels.includes('bug') && labels.includes('priority: low');
        },
    },
];

async function runUnitTests() {
    console.log('🔬 UNIT TESTS (linked-issues)');
    console.log('='.repeat(70));
    let passed = 0;
    let failed = 0;
    for (const t of unitTests) {
        try {
            const result = await Promise.resolve(t.test());
            if (result) { console.log(`✅ ${t.name}`); passed++; }
            else { console.log(`❌ ${t.name}`); failed++; }
        } catch (error) {
            console.log(`❌ ${t.name} — Error: ${error.message}`);
            failed++;
        }
    }
    console.log('\n' + '-'.repeat(70));
    console.log(`Unit Tests: ${passed} passed, ${failed} failed`);
    return { total: unitTests.length, passed, failed };
}

runTestSuite('LINKED-ISSUES TEST SUITE', [], async () => true, [
    { label: 'Unit Tests', run: runUnitTests },
]);
