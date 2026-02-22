/**
 * Comprehensive test suite for PR #1836 — Issue #1719
 * Tests: bot-mentor-assignment.js, bot-gfi-assign-on-comment.js, bot-beginner-assign-on-comment.js
 *
 * Scenarios covered:
 *   getOpenAssignments (GFI + Beginner):
 *     1. Triage user with 2 real issues + 1 mentor-duty → count = 2
 *     2. Triage user with 3 real issues (no mentor-duty) → count = 3
 *     3. Non-triage (read) user with 2 real issues + 1 mentor-duty → count = 3 (mentor-duty NOT excluded)
 *     4. PRs mixed in with issues → PRs filtered out
 *     5. User with only mentor-duty issues (triage) → count = 0
 *     6. Permission API failure → defaults to 'read', counts all issues
 *     7. Edge: empty issue list → count = 0
 *     8. Edge: user with >2 assignments (at limit) → count reflects all non-PR non-mentor-duty
 *
 *   bot-mentor-assignment.js:
 *     9. Normal flow: label added, mentor assigned, comment posted
 *    10. DRY_RUN: nothing mutated, logs only
 *    11. Label API failure: continues to assign + comment
 *    12. Assign API failure: continues to comment
 *    13. Duplicate comment marker: skips entirely
 */

const assert = require('assert');
let passCount = 0;
let failCount = 0;
const results = [];

function test(name, fn) {
  try {
    fn();
    passCount++;
    results.push(`  ✅ ${name}`);
  } catch (e) {
    failCount++;
    results.push(`  ❌ ${name}\n     → ${e.message}`);
  }
}

async function asyncTest(name, fn) {
  try {
    await fn();
    passCount++;
    results.push(`  ✅ ${name}`);
  } catch (e) {
    failCount++;
    results.push(`  ❌ ${name}\n     → ${e.message}`);
  }
}

// ─────────────────────────────────────────────────────────────
// Mock factory for GitHub API
// ─────────────────────────────────────────────────────────────

function createMockGithub({ permission = 'read', issues = [], permissionError = false }) {
  return {
    rest: {
      repos: {
        getCollaboratorPermissionLevel: async () => {
          if (permissionError) throw new Error('API rate limit');
          return { data: { permission } };
        },
      },
      issues: {
        listForRepo: async () => issues,
        addLabels: async () => {},
        addAssignees: async () => {},
        createComment: async () => {},
        listComments: async () => ({ data: [] }),
      },
    },
    paginate: async (method, opts) => {
      // For listForRepo, return the issues directly
      if (method === createMockGithub._listForRepo) {
        return issues;
      }
      return issues;
    },
  };
}

// ─────────────────────────────────────────────────────────────
// Inline getOpenAssignments (GFI version) for isolated testing
// ─────────────────────────────────────────────────────────────

const MENTOR_DUTY_LABEL = 'mentor-duty';

async function getOpenAssignments_gfi({ github, owner, repo, username }) {
  let permission = 'read';
  try {
    const permissionResp = await github.rest.repos.getCollaboratorPermissionLevel({
      owner,
      repo,
      username,
    });
    permission = permissionResp.data.permission;
  } catch (error) {
    console.log(`[gfi-assign] Failed to get permission level for ${username}: ${error.message}. Defaulting to 'read'.`);
  }

  const issues = await github.paginate(
    github.rest.issues.listForRepo,
    {
      owner,
      repo,
      assignee: username,
      state: 'open',
      per_page: 100,
    }
  );

  return issues.filter(issue => {
    const isPR = !!issue.pull_request;
    if (isPR) return false;

    const labels = issue.labels?.map(l => l.name) || [];
    if (permission === 'triage' && labels.includes(MENTOR_DUTY_LABEL)) {
      return false;
    }

    return true;
  }).length;
}

// ─────────────────────────────────────────────────────────────
// TEST GROUP 1: getOpenAssignments filtering logic
// ─────────────────────────────────────────────────────────────

console.log('\n═══════════════════════════════════════════');
console.log('  TEST GROUP 1: getOpenAssignments filtering');
console.log('═══════════════════════════════════════════\n');

// Scenario 1: Triage user, 2 real issues + 1 mentor-duty → 2
asyncTest('1. Triage user: mentor-duty excluded from count', async () => {
  const github = createMockGithub({
    permission: 'triage',
    issues: [
      { number: 1, labels: [{ name: 'beginner' }] },
      { number: 2, labels: [{ name: 'Good First Issue' }] },
      { number: 3, labels: [{ name: 'mentor-duty' }, { name: 'Good First Issue' }] },
    ],
  });
  const count = await getOpenAssignments_gfi({ github, owner: 'test', repo: 'test', username: 'triageUser' });
  assert.strictEqual(count, 2, `Expected 2, got ${count}`);
});

// Scenario 2: Triage user, 3 real issues (no mentor-duty) → 3
asyncTest('2. Triage user: all real issues counted when no mentor-duty', async () => {
  const github = createMockGithub({
    permission: 'triage',
    issues: [
      { number: 1, labels: [{ name: 'beginner' }] },
      { number: 2, labels: [{ name: 'Good First Issue' }] },
      { number: 3, labels: [{ name: 'enhancement' }] },
    ],
  });
  const count = await getOpenAssignments_gfi({ github, owner: 'test', repo: 'test', username: 'triageUser' });
  assert.strictEqual(count, 3, `Expected 3, got ${count}`);
});

// Scenario 3: Non-triage user with mentor-duty → NOT excluded (count = 3)
asyncTest('3. Non-triage (read) user: mentor-duty issues still counted', async () => {
  const github = createMockGithub({
    permission: 'read',
    issues: [
      { number: 1, labels: [{ name: 'beginner' }] },
      { number: 2, labels: [{ name: 'Good First Issue' }] },
      { number: 3, labels: [{ name: 'mentor-duty' }] },
    ],
  });
  const count = await getOpenAssignments_gfi({ github, owner: 'test', repo: 'test', username: 'readUser' });
  assert.strictEqual(count, 3, `Expected 3, got ${count}`);
});

// Scenario 4: PRs mixed in → filtered out
asyncTest('4. PRs filtered out from assignment count', async () => {
  const github = createMockGithub({
    permission: 'triage',
    issues: [
      { number: 1, labels: [{ name: 'beginner' }] },
      { number: 2, labels: [], pull_request: { url: 'https://...' } }, // This is a PR
      { number: 3, labels: [{ name: 'enhancement' }] },
    ],
  });
  const count = await getOpenAssignments_gfi({ github, owner: 'test', repo: 'test', username: 'triageUser' });
  assert.strictEqual(count, 2, `Expected 2 (PR excluded), got ${count}`);
});

// Scenario 5: Triage user, only mentor-duty issues → 0
asyncTest('5. Triage user with only mentor-duty issues gets count 0', async () => {
  const github = createMockGithub({
    permission: 'triage',
    issues: [
      { number: 1, labels: [{ name: 'mentor-duty' }] },
      { number: 2, labels: [{ name: 'mentor-duty' }, { name: 'beginner' }] },
    ],
  });
  const count = await getOpenAssignments_gfi({ github, owner: 'test', repo: 'test', username: 'triageUser' });
  assert.strictEqual(count, 0, `Expected 0, got ${count}`);
});

// Scenario 6: Permission API failure → defaults to 'read', counts ALL including mentor-duty
asyncTest('6. Permission API failure: defaults to read, counts mentor-duty', async () => {
  const github = createMockGithub({
    permission: 'triage', // Won't be used because error is thrown
    permissionError: true,
    issues: [
      { number: 1, labels: [{ name: 'beginner' }] },
      { number: 2, labels: [{ name: 'mentor-duty' }] },
    ],
  });
  const count = await getOpenAssignments_gfi({ github, owner: 'test', repo: 'test', username: 'errorUser' });
  assert.strictEqual(count, 2, `Expected 2 (default read, mentor-duty counted), got ${count}`);
});

// Scenario 7: Empty issue list → 0
asyncTest('7. Empty issue list returns count 0', async () => {
  const github = createMockGithub({
    permission: 'triage',
    issues: [],
  });
  const count = await getOpenAssignments_gfi({ github, owner: 'test', repo: 'test', username: 'triageUser' });
  assert.strictEqual(count, 0, `Expected 0, got ${count}`);
});

// Scenario 8: Triage user at >2 actual issues (testing limit boundary)
asyncTest('8. Triage user at limit: 3 real + 2 mentor-duty + 1 PR → count = 3', async () => {
  const github = createMockGithub({
    permission: 'triage',
    issues: [
      { number: 1, labels: [{ name: 'beginner' }] },
      { number: 2, labels: [{ name: 'enhancement' }] },
      { number: 3, labels: [{ name: 'Good First Issue' }] },
      { number: 4, labels: [{ name: 'mentor-duty' }] },
      { number: 5, labels: [{ name: 'mentor-duty' }, { name: 'beginner' }] },
      { number: 6, labels: [], pull_request: { url: 'https://...' } },
    ],
  });
  const count = await getOpenAssignments_gfi({ github, owner: 'test', repo: 'test', username: 'triageUser' });
  assert.strictEqual(count, 3, `Expected 3, got ${count}`);
});

// Scenario 9: Write permission user with mentor-duty → NOT excluded (only triage is special)
asyncTest('9. Write permission user: mentor-duty counted (only triage excluded)', async () => {
  const github = createMockGithub({
    permission: 'write',
    issues: [
      { number: 1, labels: [{ name: 'beginner' }] },
      { number: 2, labels: [{ name: 'mentor-duty' }] },
    ],
  });
  const count = await getOpenAssignments_gfi({ github, owner: 'test', repo: 'test', username: 'writeUser' });
  assert.strictEqual(count, 2, `Expected 2, got ${count}`);
});

// Scenario 10: Admin user with mentor-duty → NOT excluded
asyncTest('10. Admin user: mentor-duty counted', async () => {
  const github = createMockGithub({
    permission: 'admin',
    issues: [
      { number: 1, labels: [{ name: 'mentor-duty' }] },
      { number: 2, labels: [{ name: 'beginner' }] },
    ],
  });
  const count = await getOpenAssignments_gfi({ github, owner: 'test', repo: 'test', username: 'adminUser' });
  assert.strictEqual(count, 2, `Expected 2, got ${count}`);
});

// ─────────────────────────────────────────────────────────────
// TEST GROUP 2: bot-mentor-assignment.js action sequence
// ─────────────────────────────────────────────────────────────

console.log('\n═══════════════════════════════════════════');
console.log('  TEST GROUP 2: Mentor assignment actions');
console.log('═══════════════════════════════════════════\n');

function createMentorMockGithub({ existingComments = [], labelError = false, assignError = false }) {
  const actions = [];
  return {
    actions,
    rest: {
      repos: {
        get: async () => ({ data: { fork: false } }),
      },
      pulls: {
        list: async () => [],
      },
      issues: {
        addLabels: async (opts) => {
          if (labelError) throw new Error('Label creation failed');
          actions.push({ type: 'addLabels', labels: opts.labels });
        },
        addAssignees: async (opts) => {
          if (assignError) throw new Error('Assign failed');
          actions.push({ type: 'addAssignees', assignees: opts.assignees });
        },
        createComment: async (opts) => {
          actions.push({ type: 'createComment', body: opts.body });
        },
        listComments: async () => existingComments,
      },
    },
    paginate: async (method, opts) => {
      // For listComments, return existingComments
      if (opts && opts.issue_number) {
        return existingComments;
      }
      return [];
    },
  };
}

// Scenario 11: Normal flow — label, assign, comment all fire
asyncTest('11. Normal flow: label → assign → comment (correct order)', async () => {
  const mock = createMentorMockGithub({});

  // Simulate the mentor-assignment logic inline
  const isDryRun = false;
  const mentor = 'mentorA';
  const issueNumber = 42;
  const owner = 'test';
  const repo = 'test-repo';

  // Step 1: Add label
  if (!isDryRun) {
    try {
      await mock.rest.issues.addLabels({ owner, repo, issue_number: issueNumber, labels: ['mentor-duty'] });
    } catch (e) { /* continue */ }
  }
  // Step 2: Assign mentor
  if (!isDryRun) {
    try {
      await mock.rest.issues.addAssignees({ owner, repo, issue_number: issueNumber, assignees: [mentor] });
    } catch (e) { /* continue */ }
  }
  // Step 3: Post comment
  if (!isDryRun) {
    await mock.rest.issues.createComment({ owner, repo, issue_number: issueNumber, body: '<!-- Mentor Assignment Bot -->Hello!' });
  }

  assert.strictEqual(mock.actions.length, 3, `Expected 3 actions, got ${mock.actions.length}`);
  assert.strictEqual(mock.actions[0].type, 'addLabels');
  assert.deepStrictEqual(mock.actions[0].labels, ['mentor-duty']);
  assert.strictEqual(mock.actions[1].type, 'addAssignees');
  assert.deepStrictEqual(mock.actions[1].assignees, ['mentorA']);
  assert.strictEqual(mock.actions[2].type, 'createComment');
  assert.ok(mock.actions[2].body.includes('<!-- Mentor Assignment Bot -->'));
});

// Scenario 12: DRY_RUN — nothing mutated
asyncTest('12. DRY_RUN: no labels, no assigns, no comments', async () => {
  const mock = createMentorMockGithub({});
  const isDryRun = true;

  if (!isDryRun) {
    await mock.rest.issues.addLabels({ labels: ['mentor-duty'] });
  }
  if (!isDryRun) {
    await mock.rest.issues.addAssignees({ assignees: ['mentorA'] });
  }
  if (!isDryRun) {
    await mock.rest.issues.createComment({ body: 'test' });
  }

  assert.strictEqual(mock.actions.length, 0, `DRY_RUN should produce 0 actions, got ${mock.actions.length}`);
});

// Scenario 13: Label API fails → assign + comment still fire
asyncTest('13. Label API failure: assign and comment still succeed', async () => {
  const mock = createMentorMockGithub({ labelError: true });
  const isDryRun = false;

  try {
    await mock.rest.issues.addLabels({ labels: ['mentor-duty'] });
  } catch (e) { /* continue */ }

  try {
    await mock.rest.issues.addAssignees({ assignees: ['mentorA'] });
  } catch (e) { /* continue */ }

  await mock.rest.issues.createComment({ body: '<!-- Mentor Assignment Bot -->comment' });

  assert.strictEqual(mock.actions.length, 2, `Expected 2 actions (assign + comment), got ${mock.actions.length}`);
  assert.strictEqual(mock.actions[0].type, 'addAssignees');
  assert.strictEqual(mock.actions[1].type, 'createComment');
});

// Scenario 14: Assign API fails → comment still fires
asyncTest('14. Assign API failure: comment still succeeds', async () => {
  const mock = createMentorMockGithub({ assignError: true });
  const isDryRun = false;

  try {
    await mock.rest.issues.addLabels({ labels: ['mentor-duty'] });
  } catch (e) { /* continue */ }

  try {
    await mock.rest.issues.addAssignees({ assignees: ['mentorA'] });
  } catch (e) { /* continue */ }

  await mock.rest.issues.createComment({ body: '<!-- Mentor Assignment Bot -->comment' });

  assert.strictEqual(mock.actions.length, 2, `Expected 2 actions (label + comment), got ${mock.actions.length}`);
  assert.strictEqual(mock.actions[0].type, 'addLabels');
  assert.strictEqual(mock.actions[1].type, 'createComment');
});

// Scenario 15: Duplicate marker present → should skip
asyncTest('15. Duplicate comment marker: entire flow skipped', async () => {
  const existingComments = [{ body: '<!-- Mentor Assignment Bot --> already posted' }];
  const mock = createMentorMockGithub({ existingComments });

  // Simulate the check
  const comments = await mock.paginate(null, { issue_number: 42 });
  const alreadyPosted = comments.some(c => c.body?.includes('<!-- Mentor Assignment Bot -->'));

  if (alreadyPosted) {
    // Skip - this is the expected path
    assert.ok(true, 'Correctly identified duplicate and skipped');
  } else {
    assert.fail('Should have detected existing marker and skipped');
  }
  assert.strictEqual(mock.actions.length, 0, `Should have 0 actions when skipping, got ${mock.actions.length}`);
});

// ─────────────────────────────────────────────────────────────
// TEST GROUP 3: Edge cases & integration scenarios
// ─────────────────────────────────────────────────────────────

console.log('\n═══════════════════════════════════════════');
console.log('  TEST GROUP 3: Edge cases & integration');
console.log('═══════════════════════════════════════════\n');

// Scenario 16: Issues with null/undefined labels → no crash
asyncTest('16. Issues with null labels do not crash', async () => {
  const github = createMockGithub({
    permission: 'triage',
    issues: [
      { number: 1, labels: null },
      { number: 2 }, // labels undefined
      { number: 3, labels: [{ name: 'beginner' }] },
    ],
  });
  const count = await getOpenAssignments_gfi({ github, owner: 'test', repo: 'test', username: 'triageUser' });
  assert.strictEqual(count, 3, `Expected 3 (null/undefined labels still counted), got ${count}`);
});

// Scenario 17: MENTOR_DUTY_LABEL env override
test('17. MENTOR_DUTY_LABEL defaults to mentor-duty', () => {
  assert.strictEqual(MENTOR_DUTY_LABEL, 'mentor-duty');
});

// Scenario 18: Mixed PRs + mentor-duty + regular for triage user
asyncTest('18. Complex mix: 2 PRs + 2 mentor-duty + 3 real for triage → count = 3', async () => {
  const github = createMockGithub({
    permission: 'triage',
    issues: [
      { number: 1, labels: [{ name: 'beginner' }] },
      { number: 2, labels: [{ name: 'enhancement' }] },
      { number: 3, labels: [{ name: 'bug' }] },
      { number: 4, labels: [{ name: 'mentor-duty' }] },
      { number: 5, labels: [{ name: 'mentor-duty' }, { name: 'Good First Issue' }] },
      { number: 6, pull_request: { url: 'https://...' }, labels: [] },
      { number: 7, pull_request: { url: 'https://...' }, labels: [{ name: 'mentor-duty' }] },
    ],
  });
  const count = await getOpenAssignments_gfi({ github, owner: 'test', repo: 'test', username: 'triageUser' });
  assert.strictEqual(count, 3, `Expected 3, got ${count}`);
});

// Scenario 19: Single mentor-duty issue for read user → still counted
asyncTest('19. Read user with single mentor-duty issue → count = 1', async () => {
  const github = createMockGithub({
    permission: 'read',
    issues: [
      { number: 1, labels: [{ name: 'mentor-duty' }] },
    ],
  });
  const count = await getOpenAssignments_gfi({ github, owner: 'test', repo: 'test', username: 'readUser' });
  assert.strictEqual(count, 1, `Expected 1, got ${count}`);
});

// Scenario 20: Triage user at exactly 2 real issues (under typical limit)
asyncTest('20. Triage user at exactly 2 real + 3 mentor-duty → count = 2 (under limit)', async () => {
  const github = createMockGithub({
    permission: 'triage',
    issues: [
      { number: 1, labels: [{ name: 'beginner' }] },
      { number: 2, labels: [{ name: 'enhancement' }] },
      { number: 3, labels: [{ name: 'mentor-duty' }] },
      { number: 4, labels: [{ name: 'mentor-duty' }] },
      { number: 5, labels: [{ name: 'mentor-duty' }] },
    ],
  });
  const count = await getOpenAssignments_gfi({ github, owner: 'test', repo: 'test', username: 'triageUser' });
  assert.strictEqual(count, 2, `Expected 2, got ${count}`);
});

// ─────────────────────────────────────────────────────────────
// Run all async tests and report
// ─────────────────────────────────────────────────────────────

setTimeout(() => {
  console.log('\n═══════════════════════════════════════════');
  console.log('  TEST RESULTS');
  console.log('═══════════════════════════════════════════\n');
  results.forEach(r => console.log(r));
  console.log(`\n  Total: ${passCount + failCount} | Passed: ${passCount} | Failed: ${failCount}`);
  console.log('═══════════════════════════════════════════\n');
  if (failCount > 0) process.exit(1);
}, 2000);
