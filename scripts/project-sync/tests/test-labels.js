// SPDX-License-Identifier: Apache-2.0
//
// tests/test-labels.js
//
// Unit tests for helpers/labels.js (ensureLabel, ensureAllLabels).
// Run with: node .github/scripts/project-sync/tests/test-labels.js

const { runTestSuite, createMockGithub } = require('./test-utils');
const { ensureLabel, ensureAllLabels } = require('../helpers/labels');
const { ALL_MANAGED_LABELS } = require('../helpers/constants');

const unitTests = [
    {
        name: 'ensureLabel: creates label when missing',
        test: async () => {
            const mock = createMockGithub({ existingLabels: {} });
            await ensureLabel(mock, 'o', 'r', { name: 'priority: urgent', color: 'b60205', description: 'Drop everything' }, false);
            return (
                mock.calls.labelsCreated.length === 1 &&
                mock.calls.labelsCreated[0].name === 'priority: urgent'
            );
        },
    },
    {
        name: 'ensureLabel: skips when label already exists',
        test: async () => {
            const mock = createMockGithub({ existingLabels: { 'priority: urgent': true } });
            await ensureLabel(mock, 'o', 'r', { name: 'priority: urgent', color: 'b60205', description: 'Drop everything' }, false);
            return mock.calls.labelsCreated.length === 0;
        },
    },
    {
        name: 'ensureLabel: dry run does not call createLabel',
        test: async () => {
            const mock = createMockGithub({ existingLabels: {} });
            await ensureLabel(mock, 'o', 'r', { name: 'priority: high', color: 'e11d48', description: '' }, true);
            return mock.calls.labelsCreated.length === 0;
        },
    },
    {
        name: 'ensureLabel: swallows 422 on race condition',
        test: async () => {
            // Override createLabel to throw 422 to simulate a race
            const mock = createMockGithub({ existingLabels: {} });
            mock.rest.issues.createLabel = async () => {
                throw Object.assign(new Error('Already exists'), { status: 422 });
            };
            // Should not throw
            await ensureLabel(mock, 'o', 'r', { name: 'bug', color: 'd73a4a', description: '' }, false);
            return true;
        },
    },
    {
        name: 'ensureLabel: re-throws non-404 non-422 errors from getLabel',
        test: async () => {
            const mock = createMockGithub({ existingLabels: {} });
            mock.rest.issues.getLabel = async () => {
                throw Object.assign(new Error('Server error'), { status: 500 });
            };
            try {
                await ensureLabel(mock, 'o', 'r', { name: 'bug', color: '', description: '' }, false);
                return false; // should have thrown
            } catch (e) {
                return e.status === 500;
            }
        },
    },
    {
        name: 'ensureAllLabels: creates all managed labels that are missing',
        test: async () => {
            const mock = createMockGithub({ existingLabels: {} });
            await ensureAllLabels(mock, 'o', 'r', false);
            const createdNames = mock.calls.labelsCreated.map((l) => l.name);
            const expectedNames = ALL_MANAGED_LABELS.map((l) => l.name);
            return expectedNames.every((n) => createdNames.includes(n));
        },
    },
    {
        name: 'ensureAllLabels: dry run creates nothing',
        test: async () => {
            const mock = createMockGithub({ existingLabels: {} });
            await ensureAllLabels(mock, 'o', 'r', true);
            return mock.calls.labelsCreated.length === 0;
        },
    },
];

async function runUnitTests() {
    console.log('🔬 UNIT TESTS (labels)');
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

runTestSuite('LABELS TEST SUITE', [], async () => true, [
    { label: 'Unit Tests', run: runUnitTests },
]);
