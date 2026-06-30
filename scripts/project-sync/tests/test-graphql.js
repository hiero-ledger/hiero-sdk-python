// SPDX-License-Identifier: Apache-2.0
//
// tests/test-graphql.js
//
// Unit tests for helpers/graphql.js
// (addItemToProject, updateSingleSelectField, fetchProjectFields).
// Run with: node .github/scripts/project-sync/tests/test-graphql.js

const { runTestSuite, createMockGithub } = require('./test-utils');
const { addItemToProject, updateSingleSelectField, fetchProjectFields } = require('../helpers/graphql');

const unitTests = [
    // ---------------------------------------------------------------------------
    // addItemToProject
    // ---------------------------------------------------------------------------
    {
        name: 'addItemToProject: returns item node ID from mutation response',
        test: async () => {
            const mock = createMockGithub({
                graphqlResponses: [
                    { addProjectV2ItemById: { item: { id: 'PVTI_abc123' } } },
                ],
            });
            const itemId = await addItemToProject(mock, 'PVT_proj', 'PR_content');
            return itemId === 'PVTI_abc123';
        },
    },
    {
        name: 'addItemToProject: passes correct projectId and contentId variables',
        test: async () => {
            const mock = createMockGithub({
                graphqlResponses: [
                    { addProjectV2ItemById: { item: { id: 'PVTI_xyz' } } },
                ],
            });
            await addItemToProject(mock, 'PVT_myproject', 'PR_mypr');
            const call = mock.calls.graphqlCalls[0];
            return (
                call.variables.projectId === 'PVT_myproject' &&
                call.variables.contentId === 'PR_mypr'
            );
        },
    },
    {
        name: 'addItemToProject: propagates graphql errors',
        test: async () => {
            const mock = createMockGithub({
                graphqlResponses: [new Error('GraphQL error: Not Found')],
            });
            try {
                await addItemToProject(mock, 'PVT_x', 'PR_y');
                return false;
            } catch (e) {
                return e.message.includes('GraphQL error');
            }
        },
    },

    // ---------------------------------------------------------------------------
    // updateSingleSelectField
    // ---------------------------------------------------------------------------
    {
        name: 'updateSingleSelectField: passes all four required variables',
        test: async () => {
            const mock = createMockGithub({
                graphqlResponses: [
                    { updateProjectV2ItemFieldValue: { projectV2Item: { id: 'PVTI_abc' } } },
                ],
            });
            await updateSingleSelectField(mock, 'PVT_p', 'PVTI_i', 'FIELD_f', 'OPT_o');
            const call = mock.calls.graphqlCalls[0];
            return (
                call.variables.projectId === 'PVT_p' &&
                call.variables.itemId === 'PVTI_i' &&
                call.variables.fieldId === 'FIELD_f' &&
                call.variables.optionId === 'OPT_o'
            );
        },
    },
    {
        name: 'updateSingleSelectField: resolves without throwing on success',
        test: async () => {
            const mock = createMockGithub({
                graphqlResponses: [
                    { updateProjectV2ItemFieldValue: { projectV2Item: { id: 'PVTI_abc' } } },
                ],
            });
            await updateSingleSelectField(mock, 'PVT_p', 'PVTI_i', 'FIELD_f', 'OPT_o');
            return true;
        },
    },

    // ---------------------------------------------------------------------------
    // fetchProjectFields
    // ---------------------------------------------------------------------------
    {
        name: 'fetchProjectFields: builds fieldMap from graphql response',
        test: async () => {
            const mock = createMockGithub({
                graphqlResponses: [
                    {
                        node: {
                            fields: {
                                nodes: [
                                    {
                                        id: 'FIELD_priority',
                                        name: 'Priority',
                                        options: [
                                            { id: 'OPT_urgent', name: 'Urgent' },
                                            { id: 'OPT_high', name: 'High' },
                                        ],
                                    },
                                    {
                                        id: 'FIELD_type',
                                        name: 'Type',
                                        options: [
                                            { id: 'OPT_bug', name: 'Bug' },
                                            { id: 'OPT_feature', name: 'Feature' },
                                        ],
                                    },
                                    // Non-SingleSelect fields have no name — should be skipped
                                    {},
                                ],
                            },
                        },
                    },
                ],
            });
            const fields = await fetchProjectFields(mock, 'PVT_proj');
            return (
                fields['Priority'].id === 'FIELD_priority' &&
                fields['Priority'].options['Urgent'] === 'OPT_urgent' &&
                fields['Priority'].options['High'] === 'OPT_high' &&
                fields['Type'].id === 'FIELD_type' &&
                fields['Type'].options['Bug'] === 'OPT_bug' &&
                !fields['']  // empty-name node is skipped
            );
        },
    },
    {
        name: 'fetchProjectFields: returns empty map when project has no SingleSelect fields',
        test: async () => {
            const mock = createMockGithub({
                graphqlResponses: [
                    { node: { fields: { nodes: [{}, {}] } } },
                ],
            });
            const fields = await fetchProjectFields(mock, 'PVT_proj');
            return Object.keys(fields).length === 0;
        },
    },
];

async function runUnitTests() {
    console.log('🔬 UNIT TESTS (graphql)');
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

runTestSuite('GRAPHQL TEST SUITE', [], async () => true, [
    { label: 'Unit Tests', run: runUnitTests },
]);
