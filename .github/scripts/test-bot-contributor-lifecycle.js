/*
Test suite for bot-contributor-lifecycle.js

Runs the real bot against a fake octokit-shaped `github` client with in-memory
fixtures, and asserts which mutations (comments / unassign / close) would happen.

Run: node .github/scripts/test-bot-contributor-lifecycle.js
*/

const path = require("path");
const bot = require(path.join(__dirname, "bot-contributor-lifecycle.js"));

const DAY = 24 * 60 * 60 * 1000;
const daysAgo = (d) => new Date(Date.now() - d * DAY).toISOString();

let pass = 0;
let fail = 0;
const failures = [];

function check(name, cond, detail) {
  if (cond) {
    pass++;
    console.log(`  ✓ ${name}`);
  } else {
    fail++;
    failures.push(`${name}${detail ? " — " + detail : ""}`);
    console.log(`  ✗ ${name}${detail ? " — " + detail : ""}`);
  }
}

// Build a fake github client from a compact spec. Records mutations.
function makeEnv(spec) {
  const mut = { comments: [], unassigned: [], closed: [] };
  const {
    issues = [],
    commentsByIssue = {},
    graphqlByIssue = {},
    prsByNum = {},
    reviewsByPr = {},
    commitDateBySha = {},
  } = spec;

  const github = {
    paginate: async (fn, opts) => fn(opts),
    graphql: async (_query, vars) => graphqlByIssue[vars.number] || { repository: { issue: {} } },
    rest: {
      issues: {
        listForRepo: () => issues,
        listComments: ({ issue_number }) => commentsByIssue[issue_number] || [],
        createComment: async ({ issue_number, body }) => {
          mut.comments.push({ number: issue_number, body });
        },
        removeAssignees: async ({ issue_number, assignees }) => {
          mut.unassigned.push({ issue_number, assignees });
        },
      },
      pulls: {
        get: async ({ pull_number }) => {
          if (!prsByNum[pull_number]) throw new Error(`no PR ${pull_number}`);
          return { data: prsByNum[pull_number] };
        },
        listReviews: ({ pull_number }) => reviewsByPr[pull_number] || [],
        update: async ({ pull_number, state }) => {
          mut.closed.push({ pull_number, state });
        },
      },
      repos: {
        getCommit: async ({ ref }) => ({
          data: { commit: { committer: { date: commitDateBySha[ref] || daysAgo(999) } } },
        }),
      },
    },
  };

  return { github, context: { repo: { owner: "o", repo: "r" } }, mut };
}

function gqlIssue({ assignedEvents = [], prNumbers = [] }) {
  return {
    repository: {
      issue: {
        assignedEvents: { nodes: assignedEvents },
        crossRefs: {
          nodes: prNumbers.map((n) => ({
            source: { number: n, state: "OPEN", repository: { nameWithOwner: "o/r" } },
          })),
        },
        closedByPullRequestsReferences: { nodes: [] },
      },
    },
  };
}

const arr = (x) => (Array.isArray(x) ? x : [x]);

// Assigned issue with no linked PR.
function specNoPR(number, assignees, assignedDaysAgo, extraComments = []) {
  const logins = arr(assignees);
  return {
    issues: [{ number, assignees: logins.map((l) => ({ login: l })) }],
    commentsByIssue: { [number]: extraComments },
    graphqlByIssue: {
      [number]: gqlIssue({
        assignedEvents: logins.map((l) => ({ createdAt: daysAgo(assignedDaysAgo), assignee: { login: l } })),
      }),
    },
  };
}

// Assigned issue with one linked OPEN PR.
function specWithPR(issueNum, prNum, assignees, prSpec) {
  const logins = arr(assignees);
  const sha = prSpec.sha || `sha${prNum}`;
  const spec = {
    issues: [{ number: issueNum, assignees: logins.map((l) => ({ login: l })) }],
    commentsByIssue: { [issueNum]: [] },
    graphqlByIssue: {
      [issueNum]: gqlIssue({
        assignedEvents: logins.map((l) => ({ createdAt: daysAgo(120), assignee: { login: l } })),
        prNumbers: [prNum],
      }),
    },
    prsByNum: {
      [prNum]: {
        number: prNum,
        state: "open",
        user: { login: prSpec.author || "author" },
        head: { sha, repo: { owner: { login: "o" }, name: "r" } },
        labels: prSpec.labels || [],
        created_at: daysAgo(120),
      },
    },
    reviewsByPr: { [prNum]: prSpec.reviews || [] },
    commitDateBySha: { [sha]: prSpec.commitDate },
  };
  if (prSpec.prComments) spec.commentsByIssue[prNum] = prSpec.prComments;
  return spec;
}

// Assigned issue with multiple linked OPEN PRs.
// prSpecs: [{ num, author?, labels?, reviews?, commitDate, sha?, prComments? }]
function specWithPRs(issueNum, assignees, prSpecs) {
  const logins = arr(assignees);
  const spec = {
    issues: [{ number: issueNum, assignees: logins.map((l) => ({ login: l })) }],
    commentsByIssue: { [issueNum]: [] },
    graphqlByIssue: {
      [issueNum]: gqlIssue({
        assignedEvents: logins.map((l) => ({ createdAt: daysAgo(120), assignee: { login: l } })),
        prNumbers: prSpecs.map((p) => p.num),
      }),
    },
    prsByNum: {},
    reviewsByPr: {},
    commitDateBySha: {},
  };
  for (const p of prSpecs) {
    const sha = p.sha || `sha${p.num}`;
    spec.prsByNum[p.num] = {
      number: p.num,
      state: "open",
      user: { login: p.author || "author" },
      head: { sha, repo: { owner: { login: "o" }, name: "r" } },
      labels: p.labels || [],
      created_at: daysAgo(120),
    };
    spec.reviewsByPr[p.num] = p.reviews || [];
    spec.commitDateBySha[sha] = p.commitDate;
    if (p.prComments) spec.commentsByIssue[p.num] = p.prComments;
  }
  return spec;
}

const humanReview = (d) => ({ user: { login: "maintainer", type: "User" }, submitted_at: daysAgo(d) });
const botReview = (d) => ({ user: { login: "coderabbitai[bot]", type: "Bot" }, submitted_at: daysAgo(d) });

async function run(spec, env = {}) {
  for (const k of ["DRY_RUN", "ISSUE_REMIND_DAYS", "ISSUE_UNASSIGN_DAYS", "PR_REMIND_DAYS", "PR_CLOSE_DAYS", "SKIP_PR_LABELS"]) {
    delete process.env[k];
  }
  Object.assign(process.env, env);
  const { github, context, mut } = makeEnv(spec);
  const origLog = console.log;
  console.log = () => {};
  try {
    await bot({ github, context });
  } finally {
    console.log = origLog;
  }
  return mut;
}

const commentedOn = (mut, number, marker) =>
  mut.comments.some((c) => c.number === number && (!marker || c.body.includes(marker)));
const unassignedFrom = (mut, issue, login) =>
  mut.unassigned.some((u) => u.issue_number === issue && u.assignees.includes(login));

(async () => {
  console.log("=== bot-contributor-lifecycle tests ===\n");

  // 1. Issue, no PR, 10d -> remind only
  console.log("1. issue no-PR @10d -> reminder");
  let m = await run(specNoPR(101, "alice", 10), { DRY_RUN: "false" });
  check("posts issue reminder", commentedOn(m, 101, "<!-- issue-reminder-bot -->"));
  check("does not unassign", m.unassigned.length === 0);

  // 2. Issue, no PR, 30d -> unassign
  console.log("2. issue no-PR @30d -> unassign");
  m = await run(specNoPR(102, "alice", 30), { DRY_RUN: "false" });
  check("posts unassign comment", commentedOn(m, 102, "<!-- inactivity-unassign:alice -->"));
  check("unassigns the user", unassignedFrom(m, 102, "alice"));

  // 3. Issue, no PR, 30d but /working 2d ago -> keep
  console.log("3. issue no-PR @30d but /working @2d -> keep");
  m = await run(specNoPR(103, "alice", 30, [{ user: { login: "alice" }, body: "/working", created_at: daysAgo(2) }]), {
    DRY_RUN: "false",
  });
  check("no comment", m.comments.length === 0);
  check("no unassign", m.unassigned.length === 0);

  // 4. Reviewed PR, last activity 15d -> remind
  console.log("4. reviewed PR inactive @15d -> reminder");
  m = await run(specWithPR(104, 204, "alice", { author: "alice", reviews: [humanReview(15)], commitDate: daysAgo(20) }), {
    DRY_RUN: "false",
  });
  check("posts PR reminder", commentedOn(m, 204, "<!-- pr-inactivity-bot-marker -->"));
  check("does not close", m.closed.length === 0);

  // 5. Reviewed PR, last activity 70d -> close + unassign
  console.log("5. reviewed PR inactive @70d -> close + unassign");
  m = await run(specWithPR(105, 205, "alice", { author: "alice", reviews: [humanReview(70)], commitDate: daysAgo(80) }), {
    DRY_RUN: "false",
  });
  check("posts close comment", commentedOn(m, 205, "<!-- inactivity-close-bot -->"));
  check("closes the PR", m.closed.some((c) => c.pull_number === 205 && c.state === "closed"));
  check("unassigns from issue", unassignedFrom(m, 105, "alice"));

  // 6. Bot-only review, stale -> keep
  console.log("6. bot-only-reviewed stale PR -> keep");
  m = await run(specWithPR(106, 206, "alice", { author: "alice", reviews: [botReview(70)], commitDate: daysAgo(80) }), {
    DRY_RUN: "false",
  });
  check("no comment", m.comments.length === 0);
  check("no close", m.closed.length === 0);

  // 7. Reviewed stale PR but default skip label 'status: discussion' -> keep
  console.log("7. 'status: discussion'-labeled stale reviewed PR -> keep");
  m = await run(
    specWithPR(107, 207, "alice", {
      author: "alice",
      labels: [{ name: "status: discussion" }],
      reviews: [humanReview(70)],
      commitDate: daysAgo(80),
    }),
    { DRY_RUN: "false" },
  );
  check("no close", m.closed.length === 0);
  check("no comment", m.comments.length === 0);

  // 8. Dry-run mutates nothing
  console.log("8. dry-run mutates nothing");
  m = await run(specWithPR(108, 208, "alice", { author: "alice", reviews: [humanReview(70)], commitDate: daysAgo(80) }), {
    DRY_RUN: "true",
  });
  check("no comments", m.comments.length === 0);
  check("no unassign", m.unassigned.length === 0);
  check("no close", m.closed.length === 0);

  // 9. Issue reminder marker present -> no repeat
  console.log("9. issue reminder marker present -> no repeat");
  m = await run(
    specNoPR(109, "alice", 10, [
      { user: { login: "github-actions[bot]" }, body: "<!-- issue-reminder-bot -->\nold", created_at: daysAgo(3) },
    ]),
    { DRY_RUN: "false" },
  );
  check("no duplicate reminder", m.comments.length === 0);

  // 10. PR reminder marker present -> no repeat
  console.log("10. PR reminder marker present -> no repeat");
  m = await run(
    specWithPR(110, 210, "alice", {
      author: "alice",
      reviews: [humanReview(15)],
      commitDate: daysAgo(20),
      prComments: [{ user: { login: "github-actions[bot]" }, body: "<!-- pr-inactivity-bot-marker -->\nold", created_at: daysAgo(3) }],
    }),
    { DRY_RUN: "false" },
  );
  check("no duplicate PR reminder", m.comments.length === 0);

  // 11. env override PR_CLOSE_DAYS=0 -> close a fresh reviewed PR
  console.log("11. env PR_CLOSE_DAYS=0 -> close fresh reviewed PR");
  m = await run(specWithPR(111, 211, "alice", { author: "alice", reviews: [humanReview(1)], commitDate: daysAgo(1) }), {
    DRY_RUN: "false",
    PR_CLOSE_DAYS: "0",
  });
  check("closes with threshold 0", m.closed.some((c) => c.pull_number === 211));

  // 12. (B1) multi-assignee, no PR, 30d -> BOTH unassigned, each with own comment
  console.log("12. multi-assignee no-PR @30d -> both unassigned");
  m = await run(specNoPR(112, ["alice", "bob"], 30), { DRY_RUN: "false" });
  check("alice unassigned", unassignedFrom(m, 112, "alice"));
  check("bob unassigned", unassignedFrom(m, 112, "bob"));
  check("alice personal comment", commentedOn(m, 112, "<!-- inactivity-unassign:alice -->"));
  check("bob personal comment", commentedOn(m, 112, "<!-- inactivity-unassign:bob -->"));

  // 13. (B1) multi-assignee, reviewed PR stale 70d -> close once + unassign BOTH
  console.log("13. multi-assignee reviewed PR @70d -> close + unassign all");
  m = await run(specWithPR(113, 213, ["alice", "bob"], { author: "alice", reviews: [humanReview(70)], commitDate: daysAgo(80) }), {
    DRY_RUN: "false",
  });
  check("PR closed exactly once", m.closed.filter((c) => c.pull_number === 213).length === 1);
  check("alice unassigned", unassignedFrom(m, 113, "alice"));
  check("bob unassigned", unassignedFrom(m, 113, "bob"));
  check("single close comment mentions both", m.comments.filter((c) => c.number === 213).length === 1 &&
    m.comments.find((c) => c.number === 213).body.includes("@alice") &&
    m.comments.find((c) => c.number === 213).body.includes("@bob"));

  // 14. (B2) multi-assignee, no PR, 10d -> ONE combined reminder
  console.log("14. multi-assignee no-PR @10d -> single combined reminder");
  m = await run(specNoPR(114, ["alice", "bob"], 10), { DRY_RUN: "false" });
  check("exactly one reminder comment", m.comments.filter((c) => c.number === 114).length === 1);
  check("mentions both assignees", m.comments[0] && m.comments[0].body.includes("@alice") && m.comments[0].body.includes("@bob"));
  check("no unassign", m.unassigned.length === 0);

  // 15. configurable skip label via env
  console.log("15. custom SKIP_PR_LABELS env exempts a PR");
  m = await run(
    specWithPR(115, 215, "alice", {
      author: "alice",
      labels: [{ name: "needs-design" }],
      reviews: [humanReview(70)],
      commitDate: daysAgo(80),
    }),
    { DRY_RUN: "false", SKIP_PR_LABELS: "needs-design, status: blocked" },
  );
  check("custom-labeled PR not closed", m.closed.length === 0);
  check("custom-labeled PR not commented", m.comments.length === 0);

  // 16. (B3) unassign marker present -> still removes, but no duplicate comment
  console.log("16. unassign marker present -> remove without duplicate comment");
  m = await run(
    specNoPR(116, "alice", 30, [
      { user: { login: "github-actions[bot]" }, body: "<!-- inactivity-unassign:alice -->\nprev", created_at: daysAgo(1) },
    ]),
    { DRY_RUN: "false" },
  );
  check("no duplicate unassign comment", m.comments.length === 0);
  check("still attempts removal", unassignedFrom(m, 116, "alice"));

  // 17. default skip label is 'status: discussion', NOT bare 'discussion'
  console.log("17. bare 'discussion' label is NOT skipped by default");
  m = await run(
    specWithPR(117, 217, "alice", {
      author: "alice",
      labels: [{ name: "discussion" }],
      reviews: [humanReview(70)],
      commitDate: daysAgo(80),
    }),
    { DRY_RUN: "false" },
  );
  check("bare 'discussion' still closes (not a default skip label)", m.closed.some((c) => c.pull_number === 217));

  // 18. (C3) mixed: stale PR + active PR -> close stale only, keep assignment
  console.log("18. stale PR + active PR -> close stale, no unassign");
  m = await run(
    specWithPRs(118, "alice", [
      { num: 281, author: "alice", reviews: [humanReview(70)], commitDate: daysAgo(80) },
      { num: 282, author: "alice", reviews: [humanReview(5)], commitDate: daysAgo(5) },
    ]),
    { DRY_RUN: "false" },
  );
  check("stale PR 281 closed", m.closed.some((c) => c.pull_number === 281));
  check("active PR 282 not closed", !m.closed.some((c) => c.pull_number === 282));
  check("no unassign while active PR survives", m.unassigned.length === 0);
  check("close note says 'remain assigned'", (m.comments.find((c) => c.number === 281) || {}).body?.includes("remain assigned"));

  // 19. (C3) both PRs stale -> close both + unassign
  console.log("19. both PRs stale -> close both + unassign");
  m = await run(
    specWithPRs(119, "alice", [
      { num: 291, author: "alice", reviews: [humanReview(70)], commitDate: daysAgo(80) },
      { num: 292, author: "alice", reviews: [humanReview(65)], commitDate: daysAgo(70) },
    ]),
    { DRY_RUN: "false" },
  );
  check("PR 291 closed", m.closed.some((c) => c.pull_number === 291));
  check("PR 292 closed", m.closed.some((c) => c.pull_number === 292));
  check("alice unassigned", unassignedFrom(m, 119, "alice"));
  check("close note says 'unassigning you'", (m.comments.find((c) => c.number === 291) || {}).body?.includes("unassigning you"));

  // 20. (C3) stale PR + inactive (remind-stage) PR -> close stale, remind other, keep assignment
  console.log("20. stale PR + remind-stage PR -> close + remind, no unassign");
  m = await run(
    specWithPRs(120, "alice", [
      { num: 301, author: "alice", reviews: [humanReview(70)], commitDate: daysAgo(80) },
      { num: 302, author: "alice", reviews: [humanReview(15)], commitDate: daysAgo(20) },
    ]),
    { DRY_RUN: "false" },
  );
  check("PR 301 closed", m.closed.some((c) => c.pull_number === 301));
  check("PR 302 reminded", commentedOn(m, 302, "<!-- pr-inactivity-bot-marker -->"));
  check("no unassign while reminded PR survives", m.unassigned.length === 0);

  // 21. (C4) future-dated head commit is ignored -> staleness falls back to review date
  console.log("21. future-dated commit ignored -> still closes");
  m = await run(
    specWithPR(121, 321, "alice", { author: "alice", reviews: [humanReview(70)], commitDate: daysAgo(-30) }),
    { DRY_RUN: "false" },
  );
  check("future commit ignored, PR closes via review date", m.closed.some((c) => c.pull_number === 321));

  console.log(`\n=== ${pass} passed, ${fail} failed ===`);
  if (fail > 0) {
    console.log("Failures:\n - " + failures.join("\n - "));
    process.exit(1);
  }
})();
