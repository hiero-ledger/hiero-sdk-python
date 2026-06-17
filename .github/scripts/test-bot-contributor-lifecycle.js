/*
Test suite for bot-contributor-lifecycle.js

Runs the real bot against a fake octokit-shaped `github` client with in-memory
fixtures, and asserts which mutations (comments / unassign / close) would happen.

Run: node .github/scripts/test-bot-contributor-lifecycle.js
*/

const path = require("path");
const bot = require(path.join(__dirname, "bot-contributor-lifecycle.js"));

const DAY = 24 * 60 * 60 * 1000;
const iso = (msAgo) => new Date(Date.now() - msAgo).toISOString();
const daysAgo = (d) => iso(d * DAY);

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

  const context = { repo: { owner: "o", repo: "r" } };
  return { github, context, mut };
}

// A standard assigned issue with no linked PR.
function issueNoPR(number, assignee, assignedDaysAgo, extraComments = []) {
  return {
    issues: [{ number, assignees: [{ login: assignee }] }],
    commentsByIssue: { [number]: extraComments },
    graphqlByIssue: {
      [number]: {
        repository: {
          issue: {
            assignedEvents: { nodes: [{ createdAt: daysAgo(assignedDaysAgo), assignee: { login: assignee } }] },
            crossRefs: { nodes: [] },
            closedByPullRequestsReferences: { nodes: [] },
          },
        },
      },
    },
  };
}

// An assigned issue with one linked OPEN PR.
function issueWithPR(issueNum, prNum, assignee, prSpec) {
  return {
    issues: [{ number: issueNum, assignees: [{ login: assignee }] }],
    commentsByIssue: { [issueNum]: [] },
    graphqlByIssue: {
      [issueNum]: {
        repository: {
          issue: {
            assignedEvents: { nodes: [{ createdAt: daysAgo(120), assignee: { login: assignee } }] },
            crossRefs: {
              nodes: [{ source: { number: prNum, state: "OPEN", repository: { nameWithOwner: "o/r" } } }],
            },
            closedByPullRequestsReferences: { nodes: [] },
          },
        },
      },
    },
    prsByNum: {
      [prNum]: {
        number: prNum,
        state: "open",
        user: { login: prSpec.author || "author" },
        head: { sha: prSpec.sha || `sha${prNum}`, repo: { owner: { login: "o" }, name: "r" } },
        labels: prSpec.labels || [],
        created_at: daysAgo(120),
      },
    },
    reviewsByPr: { [prNum]: prSpec.reviews || [] },
    commitDateBySha: { [prSpec.sha || `sha${prNum}`]: prSpec.commitDate },
  };
}

async function run(spec, env = {}) {
  for (const k of ["DRY_RUN", "ISSUE_REMIND_DAYS", "ISSUE_UNASSIGN_DAYS", "PR_REMIND_DAYS", "PR_CLOSE_DAYS"]) {
    delete process.env[k];
  }
  Object.assign(process.env, env);
  const { github, context, mut } = makeEnv(spec);
  // silence the bot's verbose logging during tests
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

(async () => {
  console.log("=== bot-contributor-lifecycle tests ===\n");

  // 1. Issue, no PR, 10d assigned -> remind only
  console.log("1. issue no-PR @10d -> reminder");
  let m = await run(issueNoPR(101, "alice", 10), { DRY_RUN: "false" });
  check("posts issue reminder", commentedOn(m, 101, "<!-- issue-reminder-bot -->"));
  check("does not unassign", m.unassigned.length === 0);

  // 2. Issue, no PR, 30d assigned -> unassign
  console.log("2. issue no-PR @30d -> unassign");
  m = await run(issueNoPR(102, "alice", 30), { DRY_RUN: "false" });
  check("posts unassign comment", commentedOn(m, 102, "<!-- inactivity-unassign-bot -->"));
  check("unassigns the user", m.unassigned.some((u) => u.issue_number === 102 && u.assignees[0] === "alice"));

  // 3. Issue, no PR, 30d assigned but /working 2d ago -> keep
  console.log("3. issue no-PR @30d but /working @2d -> keep");
  m = await run(
    issueNoPR(103, "alice", 30, [{ user: { login: "alice" }, body: "/working", created_at: daysAgo(2) }]),
    { DRY_RUN: "false" },
  );
  check("no comment", m.comments.length === 0);
  check("no unassign", m.unassigned.length === 0);

  // 4. Reviewed PR, last activity 15d -> remind
  console.log("4. reviewed PR inactive @15d -> reminder");
  m = await run(
    issueWithPR(104, 204, "alice", {
      author: "alice",
      reviews: [{ user: { login: "maintainer", type: "User" }, submitted_at: daysAgo(15) }],
      commitDate: daysAgo(20),
    }),
    { DRY_RUN: "false" },
  );
  check("posts PR reminder", commentedOn(m, 204, "<!-- pr-inactivity-bot-marker -->"));
  check("does not close", m.closed.length === 0);

  // 5. Reviewed PR, last activity 70d -> close + unassign
  console.log("5. reviewed PR inactive @70d -> close + unassign");
  m = await run(
    issueWithPR(105, 205, "alice", {
      author: "alice",
      reviews: [{ user: { login: "maintainer", type: "User" }, submitted_at: daysAgo(70) }],
      commitDate: daysAgo(80),
    }),
    { DRY_RUN: "false" },
  );
  check("posts close comment", commentedOn(m, 205, "<!-- inactivity-close-bot -->"));
  check("closes the PR", m.closed.some((c) => c.pull_number === 205 && c.state === "closed"));
  check("unassigns from issue", m.unassigned.some((u) => u.issue_number === 105));

  // 6. PR with only a bot review, stale -> keep
  console.log("6. bot-only-reviewed stale PR -> keep");
  m = await run(
    issueWithPR(106, 206, "alice", {
      author: "alice",
      reviews: [{ user: { login: "coderabbitai[bot]", type: "Bot" }, submitted_at: daysAgo(70) }],
      commitDate: daysAgo(80),
    }),
    { DRY_RUN: "false" },
  );
  check("no comment", m.comments.length === 0);
  check("no close", m.closed.length === 0);

  // 7. Reviewed stale PR but 'discussion' label -> keep
  console.log("7. discussion-labeled stale reviewed PR -> keep");
  m = await run(
    issueWithPR(107, 207, "alice", {
      author: "alice",
      labels: [{ name: "discussion" }],
      reviews: [{ user: { login: "maintainer", type: "User" }, submitted_at: daysAgo(70) }],
      commitDate: daysAgo(80),
    }),
    { DRY_RUN: "false" },
  );
  check("no close", m.closed.length === 0);
  check("no comment", m.comments.length === 0);

  // 8. Dry-run: case-5 setup, DRY_RUN=true -> no mutations
  console.log("8. dry-run mutates nothing");
  m = await run(
    issueWithPR(108, 208, "alice", {
      author: "alice",
      reviews: [{ user: { login: "maintainer", type: "User" }, submitted_at: daysAgo(70) }],
      commitDate: daysAgo(80),
    }),
    { DRY_RUN: "true" },
  );
  check("no comments in dry run", m.comments.length === 0);
  check("no unassign in dry run", m.unassigned.length === 0);
  check("no close in dry run", m.closed.length === 0);

  // 9. Issue reminder idempotency: marker already present -> no repeat
  console.log("9. issue reminder marker present -> no repeat");
  m = await run(
    issueNoPR(109, "alice", 10, [
      { user: { login: "github-actions[bot]" }, body: "<!-- issue-reminder-bot -->\nold reminder", created_at: daysAgo(3) },
    ]),
    { DRY_RUN: "false" },
  );
  check("no duplicate reminder", m.comments.length === 0);

  // 10. PR reminder idempotency: marker already on PR -> no repeat
  console.log("10. PR reminder marker present -> no repeat");
  {
    const spec = issueWithPR(110, 210, "alice", {
      author: "alice",
      reviews: [{ user: { login: "maintainer", type: "User" }, submitted_at: daysAgo(15) }],
      commitDate: daysAgo(20),
    });
    spec.commentsByIssue[210] = [
      { user: { login: "github-actions[bot]" }, body: "<!-- pr-inactivity-bot-marker -->\nold", created_at: daysAgo(3) },
    ];
    m = await run(spec, { DRY_RUN: "false" });
    check("no duplicate PR reminder", m.comments.length === 0);
  }

  // 11. Threshold override via env (close at 0 days) -> fires immediately
  console.log("11. env override PR_CLOSE_DAYS=0 -> closes a fresh reviewed PR");
  m = await run(
    issueWithPR(111, 211, "alice", {
      author: "alice",
      reviews: [{ user: { login: "maintainer", type: "User" }, submitted_at: daysAgo(1) }],
      commitDate: daysAgo(1),
    }),
    { DRY_RUN: "false", PR_CLOSE_DAYS: "0" },
  );
  check("closes with threshold 0", m.closed.some((c) => c.pull_number === 211));

  console.log(`\n=== ${pass} passed, ${fail} failed ===`);
  if (fail > 0) {
    console.log("Failures:\n - " + failures.join("\n - "));
    process.exit(1);
  }
})();
