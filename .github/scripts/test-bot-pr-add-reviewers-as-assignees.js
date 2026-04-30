// =============================================================================
// Test: bot-pr-add-reviewers-as-assignees.js
// =============================================================================
//
// Unit tests for the reviewer → assignee bot logic with mocked GitHub API.
//
// Run with: node .github/scripts/test-bot-pr-add-reviewers-as-assignees.js

const assert = require('assert');

let addAssigneesCalls = [];
let listMembersCalls = [];
let currentPrData = null;

// Mock GitHub client with proper multi-page pagination support
const mockGithub = {
  rest: {
    pulls: {
      get: async ({ pull_number }) => ({
        data: {
          number: pull_number,
          requested_reviewers: currentPrData?.requested_reviewers || [],
          requested_teams: currentPrData?.requested_teams || [],
          assignees: currentPrData?.assignees || []
        }
      })
    },
    issues: {
      addAssignees: async (params) => {
        addAssigneesCalls.push(params);
        return { data: {} };
      }
    },
    teams: {
      listMembersInOrg: async (params) => {
        listMembersCalls.push(params.team_slug);

        // Multi-page fixture for 'test-team'
        if (params.team_slug === 'test-team') {
          const page = params.page || 1;
          const perPage = params.per_page || 30;

          const allMembers = [
            { login: 'member1' },
            { login: 'member2' },
            { login: 'member3' },
            { login: 'member4' }
          ];

          const start = (page - 1) * perPage;
          const end = Math.min(start + perPage, allMembers.length);
          const data = allMembers.slice(start, end);

          return {
            data,
            headers: end < allMembers.length
              ? { link: `<https://api.github.com/...>; rel="next"` }
              : {}
          };
        }

        if (params.team_slug === 'no-permission-team') {
          throw { status: 403, message: 'Permission denied' };
        }
        throw { status: 404, message: 'Team not found' };
      }
    }
  },

  paginate: async (operation, params) => {
    let results = [];
    let page = 1;
    let hasMore = true;

    while (hasMore) {
      const response = await operation({ ...params, page, per_page: 100 });
      const pageData = response.data || response || [];
      results = results.concat(pageData);

      hasMore = !!response.headers?.link?.includes('rel="next"');
      page++;
    }

    return results;
  }
};

const createMockContext = (payload) => ({
  repo: { owner: 'hiero-ledger', repo: 'hiero-sdk-python' },
  eventName: 'pull_request',
  payload
});

/**
 * Runs all unit tests for the reviewers-as-assignees bot.
 */
async function runTests() {
  console.log('Running tests for bot-pr-add-reviewers-as-assignees.js...\n');

  const handler = require('./bot-pr-add-reviewers-as-assignees.js');

  // Test 1: Individual reviewers
  console.log('Test 1: Individual reviewers');
  addAssigneesCalls = [];
  listMembersCalls = [];
  currentPrData = {
    requested_reviewers: [{ login: 'alice' }, { login: 'bob' }],
    requested_teams: [],
    assignees: []
  };

  const ctx1 = createMockContext({ pull_request: { number: 123, ...currentPrData } });
  process.env.DRY_RUN = 'false';
  await handler({ github: mockGithub, context: ctx1 });

  assert.strictEqual(addAssigneesCalls.length, 1);
  assert.deepStrictEqual(addAssigneesCalls[0].assignees.sort(), ['alice', 'bob']);
  console.log('✅ Passed');

  // Test 2: Team expansion
  console.log('Test 2: Team expansion');
  addAssigneesCalls = [];
  listMembersCalls = [];
  currentPrData = {
    requested_reviewers: [{ login: 'charlie' }],
    requested_teams: [{ slug: 'test-team' }],
    assignees: []
  };

  const ctx2 = createMockContext({ pull_request: { number: 124, ...currentPrData } });
  await handler({ github: mockGithub, context: ctx2 });

  assert.strictEqual(listMembersCalls.length, 1);
  assert.strictEqual(
    addAssigneesCalls[0].assignees.sort().join(','),
    'charlie,member1,member2,member3,member4'
  );
  console.log('✅ Passed');

  // Test 3: Dry run
  console.log('Test 3: Dry run mode');
  addAssigneesCalls = [];
  currentPrData = {
    requested_reviewers: [{ login: 'alice' }, { login: 'bob' }],
    requested_teams: [],
    assignees: []
  };

  const ctx3 = createMockContext({ pull_request: { number: 123, ...currentPrData } });
  process.env.DRY_RUN = 'true';
  await handler({ github: mockGithub, context: ctx3 });

  assert.strictEqual(addAssigneesCalls.length, 0);
  console.log('✅ Passed');

  // Test 4: Already assigned (deduplication)
  console.log('Test 4: Deduplication');
  addAssigneesCalls = [];
  currentPrData = {
    requested_reviewers: [{ login: 'alice' }],
    requested_teams: [],
    assignees: [{ login: 'alice' }]
  };

  const ctx4 = createMockContext({ pull_request: { number: 125, ...currentPrData } });
  process.env.DRY_RUN = 'false';
  await handler({ github: mockGithub, context: ctx4 });

  assert.strictEqual(addAssigneesCalls.length, 0);
  console.log('✅ Passed');

  // Test 5: Team expansion permission failure 
  console.log('Test 5: Team expansion permission failure');
  addAssigneesCalls = [];
  listMembersCalls = [];
  currentPrData = {
    requested_reviewers: [{ login: 'dave' }],
    requested_teams: [{ slug: 'no-permission-team' }],
    assignees: []
  };

  const ctx5 = createMockContext({ pull_request: { number: 126, ...currentPrData } });
  await handler({ github: mockGithub, context: ctx5 });

  assert.strictEqual(listMembersCalls.length, 1);
  assert.strictEqual(addAssigneesCalls[0].assignees.sort().join(','), 'dave');
  console.log('✅ Passed');

  // Test 6: Batching when >10 assignees
  console.log('Test 6: Assignee batching (>10)');
  addAssigneesCalls = [];
  currentPrData = {
    requested_reviewers: Array.from({ length: 15 }, (_, i) => ({ login: `user${i}` })),
    requested_teams: [],
    assignees: []
  };

  const ctx6 = createMockContext({ pull_request: { number: 127, ...currentPrData } });
  await handler({ github: mockGithub, context: ctx6 });

  assert.strictEqual(addAssigneesCalls.length, 2, 'Should make 2 batch calls for 15 users');
  assert.strictEqual(addAssigneesCalls[0].assignees.length, 10);
  assert.strictEqual(addAssigneesCalls[1].assignees.length, 5);
  assert.deepStrictEqual(
    addAssigneesCalls.flatMap(call => call.assignees).sort(),
    Array.from({ length: 15 }, (_, i) => `user${i}`).sort()
  );
  console.log('✅ Passed');

  // Test 7: Manual workflow_dispatch path
  console.log('Test 7: workflow_dispatch');
  addAssigneesCalls = [];
  currentPrData = {
    requested_reviewers: [{ login: 'eve' }],
    requested_teams: [],
    assignees: []
  };

  const ctx7 = {
    repo: { owner: 'hiero-ledger', repo: 'hiero-sdk-python' },
    eventName: 'workflow_dispatch',
    payload: { inputs: { pr_number: '128' } }
  };
  process.env.DRY_RUN = 'false';
  await handler({ github: mockGithub, context: ctx7 });

  assert.strictEqual(addAssigneesCalls.length, 1);
  assert.strictEqual(addAssigneesCalls[0].issue_number, 128);
  assert.deepStrictEqual(addAssigneesCalls[0].assignees.sort(), ['eve']);
  console.log('✅ Passed');

  // Test 8: No reviewers or teams
  console.log('Test 8: No reviewers or teams');
  addAssigneesCalls = [];
  currentPrData = {
    requested_reviewers: [],
    requested_teams: [],
    assignees: []
  };

  const ctx8 = createMockContext({ pull_request: { number: 129, ...currentPrData } });
  process.env.DRY_RUN = 'false';
  await handler({ github: mockGithub, context: ctx8 });

  assert.strictEqual(addAssigneesCalls.length, 0);
  console.log('✅ Passed');

  // Test 9: Multi-page team expansion (pagination)
  console.log('Test 9: Multi-page team expansion');
  addAssigneesCalls = [];
  listMembersCalls = [];
  currentPrData = {
    requested_reviewers: [{ login: 'charlie' }],
    requested_teams: [{ slug: 'test-team' }],
    assignees: []
  };

  const ctx9 = createMockContext({ pull_request: { number: 130, ...currentPrData } });
  await handler({ github: mockGithub, context: ctx9 });

  assert.strictEqual(listMembersCalls.length, 1);
  assert.strictEqual(
    addAssigneesCalls[0].assignees.sort().join(','),
    'charlie,member1,member2,member3,member4'
  );
  console.log('✅ Passed');

  // Test 10: addAssignees 403 permission failure (partial assignment)
  console.log('Test 10: addAssignees 403 permission failure');
  addAssigneesCalls = [];
  currentPrData = {
    requested_reviewers: Array.from({ length: 15 }, (_, i) => ({ login: `user${i}` })),
    requested_teams: [],
    assignees: []
  };

  let addAssigneesCallCount = 0;
  const mockGithubWith403 = {
    ...mockGithub,
    rest: {
      ...mockGithub.rest,
      issues: {
        addAssignees: async (params) => {
          addAssigneesCalls.push(params);
          addAssigneesCallCount++;
          if (addAssigneesCallCount === 2) {
            throw { status: 403, message: 'Permission denied' };
          }
          return { data: {} };
        }
      }
    }
  };

  const ctx10 = createMockContext({ pull_request: { number: 131, ...currentPrData } });
  await handler({ github: mockGithubWith403, context: ctx10 });

  assert.strictEqual(addAssigneesCalls.length, 2, 'Should stop after 403 on second batch');
  assert.strictEqual(addAssigneesCalls[0].assignees.length, 10, 'First batch should have 10');
  console.log('✅ Passed');

  console.log('\n🎉 All tests passed!');
}

runTests().catch(err => {
  console.error('❌ Test failed:', err.message);
  process.exit(1);
});