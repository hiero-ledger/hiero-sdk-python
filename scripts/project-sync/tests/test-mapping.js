// SPDX-License-Identifier: Apache-2.0
//
// tests/test-mapping.js
//
// Unit tests for helpers/mapping.js (deriveFieldValues).
// Run with: node .github/scripts/project-sync/tests/test-mapping.js

const { runTestSuite } = require('./test-utils');
const { deriveFieldValues } = require('../helpers/mapping');

const unitTests = [
    {
        name: 'deriveFieldValues: no labels → { priority: null, type: null }',
        test: () => {
            const r = deriveFieldValues([]);
            return r.priority === null && r.type === null;
        },
    },
    {
        name: 'deriveFieldValues: unrelated labels → { priority: null, type: null }',
        test: () => {
            const r = deriveFieldValues(['skill: beginner', 'help wanted', 'Good First Issue']);
            return r.priority === null && r.type === null;
        },
    },
    {
        name: 'deriveFieldValues: "priority: urgent" → priority "Urgent"',
        test: () => {
            const r = deriveFieldValues(['priority: urgent']);
            return r.priority === 'Urgent' && r.type === null;
        },
    },
    {
        name: 'deriveFieldValues: "priority: high" → priority "High"',
        test: () => {
            const r = deriveFieldValues(['priority: high']);
            return r.priority === 'High';
        },
    },
    {
        name: 'deriveFieldValues: "priority: medium" → priority "Medium"',
        test: () => {
            const r = deriveFieldValues(['priority: medium']);
            return r.priority === 'Medium';
        },
    },
    {
        name: 'deriveFieldValues: "priority: low" → priority "Low"',
        test: () => {
            const r = deriveFieldValues(['priority: low']);
            return r.priority === 'Low';
        },
    },
    {
        name: 'deriveFieldValues: "bug" → type "Bug"',
        test: () => {
            const r = deriveFieldValues(['bug']);
            return r.type === 'Bug' && r.priority === null;
        },
    },
    {
        name: 'deriveFieldValues: "feature" → type "Feature"',
        test: () => {
            const r = deriveFieldValues(['feature']);
            return r.type === 'Feature' && r.priority === null;
        },
    },
    {
        name: 'deriveFieldValues: both priority and type present',
        test: () => {
            const r = deriveFieldValues(['priority: high', 'bug']);
            return r.priority === 'High' && r.type === 'Bug';
        },
    },
    {
        name: 'deriveFieldValues: urgent wins over high when both present',
        test: () => {
            const r = deriveFieldValues(['priority: high', 'priority: urgent']);
            return r.priority === 'Urgent';
        },
    },
    {
        name: 'deriveFieldValues: bug wins over feature when both present',
        test: () => {
            const r = deriveFieldValues(['feature', 'bug']);
            return r.type === 'Bug';
        },
    },
    {
        name: 'deriveFieldValues: label comparison is case-insensitive',
        test: () => {
            const r = deriveFieldValues(['Priority: Urgent', 'Bug']);
            return r.priority === 'Urgent' && r.type === 'Bug';
        },
    },
    {
        name: 'deriveFieldValues: mixed casing with extra labels',
        test: () => {
            const r = deriveFieldValues(['skill: intermediate', 'PRIORITY: HIGH', 'enhancement']);
            return r.priority === 'High' && r.type === null;
        },
    },
];

async function runUnitTests() {
    console.log('🔬 UNIT TESTS (mapping)');
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

runTestSuite('MAPPING TEST SUITE', [], async () => true, [
    { label: 'Unit Tests', run: runUnitTests },
]);
