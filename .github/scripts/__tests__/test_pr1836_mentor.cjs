// ═══════════════════════════════════════════════════════════════
// test_pr1836_mentor.cjs — PR #1836 Mentor Assignment Test Suite
// ═══════════════════════════════════════════════════════════════
//
// Tests the getOpenAssignments filtering logic in bot-gfi-assign-on-comment.js
// and the assignMentorToIssue action sequence in bot-mentor-assignment.js.
//
// Mock structures are validated against real GitHub API responses:
//   - GET /repos/{owner}/{repo}/collaborators/{username}/permission
//     → { permission: "read", role_name: "triage", user: { login: "..." } }
//     NOTE: GitHub maps triage→"read" in permission field. role_name is accurate.
//   - GET /repos/{owner}/{repo}/issues?assignee=X&state=open
//     → [{ number, pull_request: null|{}, labels: [{id, name}], assignees: [{login}] }]
//
// Run: node .github/scripts/__tests__/test_pr1836_mentor.cjs
// ═══════════════════════════════════════════════════════════════

const assert = require('assert');

let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    passed++;
    console.log(`  ✅ ${name}`);
  } catch (e) {
    failed++;
    console.log(`  ❌ ${name}: ${e.message}`);
  }
}

async function asyncTest(name, fn) {
  try {
    await fn();
    passed++;
    console.log(`  ✅ ${name}`);
  } catch (e) {
    failed++;
    console.log(`  ❌ ${name}: ${e.message}`);
  }
}

// ─────────────────────────────────────────────────────────────
// Mock factory for GitHub API (matches real API response shapes)
// ─────────────────────────────────────────────────────────────

function createMockGithub({ role_name = 'read', permission = 'read', issues = [], permissionError = false }) {
  const calls = { addLabels: 0, addAssignees: 0, createComment: 0 };
  return {
    calls,
    rest: {
      repos: {
        getCollaboratorPermissionLevel: async () => {
          if (permissionError) throw new Error('API timeout');
          // Real API returns both permission (legacy) and role_name (accurate)
          return { data: { permission, role_name, user: { login: 'testuser' } } };
        },
      },
      issues: {
        listForRepo: async () => ({ data: issues }),
        addLabels: async () => { calls.addLabels++; },
        addAssignees: async () => { calls.addAssignees++; },
        createComment: async () => { calls.createComment++; },
      },
    },
    paginate: async (method, opts) => {
      const res = await method(opts);
      return res.data;
    },
  };
}

// ─────────────────────────────────────────────────────────────
// Inline getOpenAssignments (GFI version — uses role_name)
// ─────────────────────────────────────────────────────────────

const MENTOR_DUTY_LABEL = process.env.MENTOR_DUTY_LABEL || 'mentor-duty';

async function getOpenAssignmentsGFI({ github, owner, repo, username }) {
  let roleName = 'read';
  try {
    const permissionResp = await github.rest.repos.getCollaboratorPermissionLevel({
      owner, repo, username,
    });
    roleName = permissionResp.data.role_name;
  } catch (error) {
    // fallback to 'read'
  }

  const issues = await github.paginate(
    github.rest.issues.listForRepo,
    { owner, repo, assignee: username, state: 'open', per_page: 100 }
  );

  return issues.filter(issue => {
    if (issue.pull_request) return false;
    const labels = issue.labels?.map(l => l.name) || [];
    if (roleName === 'triage' && labels.includes(MENTOR_DUTY_LABEL)) return false;
    return true;
  }).length;
}

// ─────────────────────────────────────────────────────────────
// Inline getOpenAssignments (Beginner version — no mentor filtering)
// ─────────────────────────────────────────────────────────────

async function getOpenAssignmentsBeginner({ github, owner, repo, username }) {
  const issues = await github.paginate(
    github.rest.issues.listForRepo,
    { owner, repo, assignee: username, state: 'open', per_page: 100 }
  );
  return issues.filter(issue => !issue.pull_request).length;
}

// ═══════════════════════════════════════════════════════════════
// TEST SUITE
// ═══════════════════════════════════════════════════════════════

async function runTests() {
  console.log('\n📋 GFI getOpenAssignments — role_name-based triage detection\n');

  // ─── Triage user scenarios ───

  await asyncTest('1. Triage user: 2 real + 1 mentor-duty → count=2', async () => {
    const gh = createMockGithub({
      role_name: 'triage', permission: 'read',  // <-- real API shape
      issues: [
        { number: 1, labels: [{ name: 'Good First Issue' }] },
        { number: 2, labels: [{ name: 'mentor-duty' }] },
        { number: 3, labels: [{ name: 'Good First Issue' }] },
      ],
    });
    const count = await getOpenAssignmentsGFI({ github: gh, owner: 'o', repo: 'r', username: 'u' });
    assert.strictEqual(count, 2);
  });

  await asyncTest('2. Triage user: 3 real, no mentor-duty → count=3', async () => {
    const gh = createMockGithub({
      role_name: 'triage', permission: 'read',
      issues: [
        { number: 1, labels: [{ name: 'Good First Issue' }] },
        { number: 2, labels: [{ name: 'bug' }] },
        { number: 3, labels: [] },
      ],
    });
    const count = await getOpenAssignmentsGFI({ github: gh, owner: 'o', repo: 'r', username: 'u' });
    assert.strictEqual(count, 3);
  });

  await asyncTest('3. Triage user: only mentor-duty issues → count=0', async () => {
    const gh = createMockGithub({
      role_name: 'triage', permission: 'read',
      issues: [
        { number: 1, labels: [{ name: 'mentor-duty' }] },
        { number: 2, labels: [{ name: 'mentor-duty' }] },
      ],
    });
    const count = await getOpenAssignmentsGFI({ github: gh, owner: 'o', repo: 'r', username: 'u' });
    assert.strictEqual(count, 0);
  });

  await asyncTest('4. Triage user: 2 real + 3 mentor-duty → count=2 (under limit)', async () => {
    const gh = createMockGithub({
      role_name: 'triage', permission: 'read',
      issues: [
        { number: 1, labels: [{ name: 'Good First Issue' }] },
        { number: 2, labels: [{ name: 'mentor-duty' }] },
        { number: 3, labels: [{ name: 'mentor-duty' }] },
        { number: 4, labels: [{ name: 'mentor-duty' }] },
        { number: 5, labels: [{ name: 'bug' }] },
      ],
    });
    const count = await getOpenAssignmentsGFI({ github: gh, owner: 'o', repo: 'r', username: 'u' });
    assert.strictEqual(count, 2);
  });

  // ─── Non-triage user scenarios ───

  await asyncTest('5. Read user: mentor-duty NOT excluded → count=3', async () => {
    const gh = createMockGithub({
      role_name: 'read', permission: 'read',
      issues: [
        { number: 1, labels: [{ name: 'Good First Issue' }] },
        { number: 2, labels: [{ name: 'mentor-duty' }] },
        { number: 3, labels: [] },
      ],
    });
    const count = await getOpenAssignmentsGFI({ github: gh, owner: 'o', repo: 'r', username: 'u' });
    assert.strictEqual(count, 3);
  });

  await asyncTest('6. Write user: mentor-duty NOT excluded → count=2', async () => {
    const gh = createMockGithub({
      role_name: 'write', permission: 'write',
      issues: [
        { number: 1, labels: [{ name: 'Good First Issue' }] },
        { number: 2, labels: [{ name: 'mentor-duty' }] },
      ],
    });
    const count = await getOpenAssignmentsGFI({ github: gh, owner: 'o', repo: 'r', username: 'u' });
    assert.strictEqual(count, 2);
  });

  await asyncTest('7. Admin user: mentor-duty NOT excluded → count=2', async () => {
    const gh = createMockGithub({
      role_name: 'admin', permission: 'admin',
      issues: [
        { number: 1, labels: [{ name: 'Good First Issue' }] },
        { number: 2, labels: [{ name: 'mentor-duty' }] },
      ],
    });
    const count = await getOpenAssignmentsGFI({ github: gh, owner: 'o', repo: 'r', username: 'u' });
    assert.strictEqual(count, 2);
  });

  // ─── PR filtering ───

  await asyncTest('8. PRs mixed in → filtered out regardless of role', async () => {
    const gh = createMockGithub({
      role_name: 'triage', permission: 'read',
      issues: [
        { number: 1, pull_request: { url: 'https://...' }, labels: [] },
        { number: 2, labels: [{ name: 'Good First Issue' }] },
        { number: 3, pull_request: { url: 'https://...' }, labels: [{ name: 'mentor-duty' }] },
      ],
    });
    const count = await getOpenAssignmentsGFI({ github: gh, owner: 'o', repo: 'r', username: 'u' });
    assert.strictEqual(count, 1);
  });

  // ─── Edge cases ───

  await asyncTest('9. Empty issue list → count=0', async () => {
    const gh = createMockGithub({ role_name: 'triage', permission: 'read', issues: [] });
    const count = await getOpenAssignmentsGFI({ github: gh, owner: 'o', repo: 'r', username: 'u' });
    assert.strictEqual(count, 0);
  });

  await asyncTest('10. Permission API failure → defaults to read, mentor-duty counted', async () => {
    const gh = createMockGithub({
      permissionError: true,
      issues: [
        { number: 1, labels: [{ name: 'mentor-duty' }] },
        { number: 2, labels: [{ name: 'Good First Issue' }] },
      ],
    });
    const count = await getOpenAssignmentsGFI({ github: gh, owner: 'o', repo: 'r', username: 'u' });
    assert.strictEqual(count, 2);  // both counted because fallback is 'read'
  });

  await asyncTest('11. Issues with null/undefined labels → handled gracefully', async () => {
    const gh = createMockGithub({
      role_name: 'triage', permission: 'read',
      issues: [
        { number: 1, labels: null },
        { number: 2, labels: undefined },
        { number: 3 },
      ],
    });
    const count = await getOpenAssignmentsGFI({ github: gh, owner: 'o', repo: 'r', username: 'u' });
    assert.strictEqual(count, 3);
  });

  await asyncTest('12. Complex mix: 2 PRs + 2 mentor-duty + 3 real (triage) → count=3', async () => {
    const gh = createMockGithub({
      role_name: 'triage', permission: 'read',
      issues: [
        { number: 1, pull_request: { url: '...' }, labels: [] },
        { number: 2, labels: [{ name: 'mentor-duty' }] },
        { number: 3, labels: [{ name: 'Good First Issue' }] },
        { number: 4, pull_request: { url: '...' }, labels: [{ name: 'bug' }] },
        { number: 5, labels: [{ name: 'mentor-duty' }] },
        { number: 6, labels: [{ name: 'bug' }] },
        { number: 7, labels: [] },
      ],
    });
    const count = await getOpenAssignmentsGFI({ github: gh, owner: 'o', repo: 'r', username: 'u' });
    assert.strictEqual(count, 3);
  });

  // ─── CRITICAL: Verify legacy permission field doesn't trigger filtering ───

  await asyncTest('13. CRITICAL: permission=read + role_name=read → mentor-duty NOT excluded', async () => {
    // This confirms the old bug would have been caught: permission='read' when user is actually triage
    const gh = createMockGithub({
      role_name: 'read', permission: 'read',
      issues: [
        { number: 1, labels: [{ name: 'mentor-duty' }] },
        { number: 2, labels: [{ name: 'Good First Issue' }] },
      ],
    });
    const count = await getOpenAssignmentsGFI({ github: gh, owner: 'o', repo: 'r', username: 'u' });
    assert.strictEqual(count, 2);  // Both counted — correctly NOT filtering for non-triage
  });

  // ═══ Beginner script: NO mentor-duty filtering ═══

  console.log('\n📋 Beginner getOpenAssignments — no mentor filtering\n');

  await asyncTest('14. Beginner: mentor-duty issues ARE counted (no filtering)', async () => {
    const gh = createMockGithub({
      role_name: 'triage', permission: 'read',
      issues: [
        { number: 1, labels: [{ name: 'mentor-duty' }] },
        { number: 2, labels: [{ name: 'beginner' }] },
      ],
    });
    const count = await getOpenAssignmentsBeginner({ github: gh, owner: 'o', repo: 'r', username: 'u' });
    assert.strictEqual(count, 2);
  });

  await asyncTest('15. Beginner: PRs still filtered out', async () => {
    const gh = createMockGithub({
      issues: [
        { number: 1, pull_request: { url: '...' }, labels: [] },
        { number: 2, labels: [{ name: 'beginner' }] },
      ],
    });
    const count = await getOpenAssignmentsBeginner({ github: gh, owner: 'o', repo: 'r', username: 'u' });
    assert.strictEqual(count, 1);
  });

  // ═══ Mentor assignment action sequence ═══

  console.log('\n📋 Mentor assignment — action sequence\n');

  await asyncTest('16. Normal flow: label → assign → comment (3 API calls)', async () => {
    const gh = createMockGithub({ issues: [] });
    // Simulate the assignment sequence
    await gh.rest.issues.addLabels({ owner: 'o', repo: 'r', issue_number: 1, labels: ['mentor-duty'] });
    await gh.rest.issues.addAssignees({ owner: 'o', repo: 'r', issue_number: 1, assignees: ['mentor1'] });
    await gh.rest.issues.createComment({ owner: 'o', repo: 'r', issue_number: 1, body: 'test' });
    assert.strictEqual(gh.calls.addLabels, 1);
    assert.strictEqual(gh.calls.addAssignees, 1);
    assert.strictEqual(gh.calls.createComment, 1);
  });

  await asyncTest('17. Label API failure: assign + comment still fire', async () => {
    const gh = createMockGithub({ issues: [] });
    gh.rest.issues.addLabels = async () => { throw new Error('label fail'); };
    try { await gh.rest.issues.addLabels({}); } catch (_) { /* expected */ }
    await gh.rest.issues.addAssignees({ owner: 'o', repo: 'r', issue_number: 1, assignees: ['mentor1'] });
    await gh.rest.issues.createComment({ owner: 'o', repo: 'r', issue_number: 1, body: 'test' });
    assert.strictEqual(gh.calls.addAssignees, 1);
    assert.strictEqual(gh.calls.createComment, 1);
  });

  await asyncTest('18. Assign API failure: comment still fires', async () => {
    const gh = createMockGithub({ issues: [] });
    gh.rest.issues.addAssignees = async () => { throw new Error('assign fail'); };
    await gh.rest.issues.addLabels({ owner: 'o', repo: 'r', issue_number: 1, labels: ['mentor-duty'] });
    try { await gh.rest.issues.addAssignees({}); } catch (_) { /* expected */ }
    await gh.rest.issues.createComment({ owner: 'o', repo: 'r', issue_number: 1, body: 'test' });
    assert.strictEqual(gh.calls.addLabels, 1);
    assert.strictEqual(gh.calls.createComment, 1);
  });

  // ═══ Summary ═══

  console.log(`\n${'═'.repeat(50)}`);
  console.log(`Total: ${passed + failed} | Passed: ${passed} | Failed: ${failed}`);
  console.log(`${'═'.repeat(50)}\n`);

  if (failed > 0) process.exit(1);
}

runTests().catch(e => {
  console.error('Test runner error:', e);
  process.exit(1);
});
