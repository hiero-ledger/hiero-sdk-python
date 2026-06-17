// SPDX-License-Identifier: Apache-2.0

/**
 * @fileoverview
 * Unit tests for bot-contributor-lifecycle.js. Runs the real handler against a
 * fake octokit-shaped `github` client with in-memory fixtures and asserts which
 * mutations (comments / unassign / close) would happen.
 */

const bot = require("../bot-contributor-lifecycle.js");

const DAY = 24 * 60 * 60 * 1000;
const daysAgo = (d) => new Date(Date.now() - d * DAY).toISOString();

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
  return specWithPRs(issueNum, assignees, [{ num: prNum, ...prSpec }]);
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

const THRESHOLD_KEYS = ["DRY_RUN", "ISSUE_REMIND_DAYS", "ISSUE_UNASSIGN_DAYS", "PR_REMIND_DAYS", "PR_CLOSE_DAYS", "SKIP_PR_LABELS"];

async function run(spec, env = {}) {
  for (const k of THRESHOLD_KEYS) delete process.env[k];
  Object.assign(process.env, env);
  const { github, context, mut } = makeEnv(spec);
  const spy = jest.spyOn(console, "log").mockImplementation(() => {});
  try {
    await bot({ github, context });
  } finally {
    spy.mockRestore();
  }
  return mut;
}

const commentedOn = (mut, number, marker) =>
  mut.comments.some((c) => c.number === number && (!marker || c.body.includes(marker)));
const unassignedFrom = (mut, issue, login) =>
  mut.unassigned.some((u) => u.issue_number === issue && u.assignees.includes(login));

describe("bot-contributor-lifecycle", () => {
  afterEach(() => {
    for (const k of THRESHOLD_KEYS) delete process.env[k];
  });

  test("issue, no PR, 10d -> reminder only", async () => {
    const m = await run(specNoPR(101, "alice", 10), { DRY_RUN: "false" });
    expect(commentedOn(m, 101, "<!-- issue-reminder-bot -->")).toBe(true);
    expect(m.unassigned).toHaveLength(0);
  });

  test("issue, no PR, 30d -> unassign", async () => {
    const m = await run(specNoPR(102, "alice", 30), { DRY_RUN: "false" });
    expect(commentedOn(m, 102, "<!-- inactivity-unassign:alice -->")).toBe(true);
    expect(unassignedFrom(m, 102, "alice")).toBe(true);
  });

  test("issue, no PR, 30d but /working 2d ago -> keep", async () => {
    const m = await run(
      specNoPR(103, "alice", 30, [{ user: { login: "alice" }, body: "/working", created_at: daysAgo(2) }]),
      { DRY_RUN: "false" },
    );
    expect(m.comments).toHaveLength(0);
    expect(m.unassigned).toHaveLength(0);
  });

  test("reviewed PR inactive 15d -> reminder", async () => {
    const m = await run(specWithPR(104, 204, "alice", { author: "alice", reviews: [humanReview(15)], commitDate: daysAgo(20) }), {
      DRY_RUN: "false",
    });
    expect(commentedOn(m, 204, "<!-- pr-inactivity-bot-marker -->")).toBe(true);
    expect(m.closed).toHaveLength(0);
  });

  test("reviewed PR inactive 70d -> close + unassign", async () => {
    const m = await run(specWithPR(105, 205, "alice", { author: "alice", reviews: [humanReview(70)], commitDate: daysAgo(80) }), {
      DRY_RUN: "false",
    });
    expect(commentedOn(m, 205, "<!-- inactivity-close-bot -->")).toBe(true);
    expect(m.closed.some((c) => c.pull_number === 205 && c.state === "closed")).toBe(true);
    expect(unassignedFrom(m, 105, "alice")).toBe(true);
  });

  test("bot-only-reviewed stale PR -> keep", async () => {
    const m = await run(specWithPR(106, 206, "alice", { author: "alice", reviews: [botReview(70)], commitDate: daysAgo(80) }), {
      DRY_RUN: "false",
    });
    expect(m.comments).toHaveLength(0);
    expect(m.closed).toHaveLength(0);
  });

  test("'status: discussion'-labeled stale reviewed PR -> keep (default skip label)", async () => {
    const m = await run(
      specWithPR(107, 207, "alice", {
        author: "alice",
        labels: [{ name: "status: discussion" }],
        reviews: [humanReview(70)],
        commitDate: daysAgo(80),
      }),
      { DRY_RUN: "false" },
    );
    expect(m.closed).toHaveLength(0);
    expect(m.comments).toHaveLength(0);
  });

  test("dry-run mutates nothing", async () => {
    const m = await run(specWithPR(108, 208, "alice", { author: "alice", reviews: [humanReview(70)], commitDate: daysAgo(80) }), {
      DRY_RUN: "true",
    });
    expect(m.comments).toHaveLength(0);
    expect(m.unassigned).toHaveLength(0);
    expect(m.closed).toHaveLength(0);
  });

  test("issue reminder marker present -> no repeat", async () => {
    const m = await run(
      specNoPR(109, "alice", 10, [
        { user: { login: "github-actions[bot]" }, body: "<!-- issue-reminder-bot -->\nold", created_at: daysAgo(3) },
      ]),
      { DRY_RUN: "false" },
    );
    expect(m.comments).toHaveLength(0);
  });

  test("PR reminder marker present -> no repeat", async () => {
    const m = await run(
      specWithPR(110, 210, "alice", {
        author: "alice",
        reviews: [humanReview(15)],
        commitDate: daysAgo(20),
        prComments: [{ user: { login: "github-actions[bot]" }, body: "<!-- pr-inactivity-bot-marker -->\nold", created_at: daysAgo(3) }],
      }),
      { DRY_RUN: "false" },
    );
    expect(m.comments).toHaveLength(0);
  });

  test("env PR_CLOSE_DAYS=0 -> closes fresh reviewed PR", async () => {
    const m = await run(specWithPR(111, 211, "alice", { author: "alice", reviews: [humanReview(1)], commitDate: daysAgo(1) }), {
      DRY_RUN: "false",
      PR_CLOSE_DAYS: "0",
    });
    expect(m.closed.some((c) => c.pull_number === 211)).toBe(true);
  });

  test("multi-assignee no-PR 30d -> both unassigned with own comment", async () => {
    const m = await run(specNoPR(112, ["alice", "bob"], 30), { DRY_RUN: "false" });
    expect(unassignedFrom(m, 112, "alice")).toBe(true);
    expect(unassignedFrom(m, 112, "bob")).toBe(true);
    expect(commentedOn(m, 112, "<!-- inactivity-unassign:alice -->")).toBe(true);
    expect(commentedOn(m, 112, "<!-- inactivity-unassign:bob -->")).toBe(true);
  });

  test("multi-assignee reviewed PR 70d -> close once + unassign all", async () => {
    const m = await run(specWithPR(113, 213, ["alice", "bob"], { author: "alice", reviews: [humanReview(70)], commitDate: daysAgo(80) }), {
      DRY_RUN: "false",
    });
    expect(m.closed.filter((c) => c.pull_number === 213)).toHaveLength(1);
    expect(unassignedFrom(m, 113, "alice")).toBe(true);
    expect(unassignedFrom(m, 113, "bob")).toBe(true);
    const closeComment = m.comments.find((c) => c.number === 213);
    expect(m.comments.filter((c) => c.number === 213)).toHaveLength(1);
    expect(closeComment.body).toContain("@alice");
    expect(closeComment.body).toContain("@bob");
  });

  test("multi-assignee no-PR 10d -> single combined reminder", async () => {
    const m = await run(specNoPR(114, ["alice", "bob"], 10), { DRY_RUN: "false" });
    expect(m.comments.filter((c) => c.number === 114)).toHaveLength(1);
    expect(m.comments[0].body).toContain("@alice");
    expect(m.comments[0].body).toContain("@bob");
    expect(m.unassigned).toHaveLength(0);
  });

  test("custom SKIP_PR_LABELS env exempts a PR", async () => {
    const m = await run(
      specWithPR(115, 215, "alice", {
        author: "alice",
        labels: [{ name: "needs-design" }],
        reviews: [humanReview(70)],
        commitDate: daysAgo(80),
      }),
      { DRY_RUN: "false", SKIP_PR_LABELS: "needs-design, status: blocked" },
    );
    expect(m.closed).toHaveLength(0);
    expect(m.comments).toHaveLength(0);
  });

  test("unassign marker present -> remove without duplicate comment", async () => {
    const m = await run(
      specNoPR(116, "alice", 30, [
        { user: { login: "github-actions[bot]" }, body: "<!-- inactivity-unassign:alice -->\nprev", created_at: daysAgo(1) },
      ]),
      { DRY_RUN: "false" },
    );
    expect(m.comments).toHaveLength(0);
    expect(unassignedFrom(m, 116, "alice")).toBe(true);
  });

  test("bare 'discussion' label is NOT skipped by default", async () => {
    const m = await run(
      specWithPR(117, 217, "alice", {
        author: "alice",
        labels: [{ name: "discussion" }],
        reviews: [humanReview(70)],
        commitDate: daysAgo(80),
      }),
      { DRY_RUN: "false" },
    );
    expect(m.closed.some((c) => c.pull_number === 217)).toBe(true);
  });

  test("stale PR + active PR -> close stale only, keep assignment", async () => {
    const m = await run(
      specWithPRs(118, "alice", [
        { num: 281, author: "alice", reviews: [humanReview(70)], commitDate: daysAgo(80) },
        { num: 282, author: "alice", reviews: [humanReview(5)], commitDate: daysAgo(5) },
      ]),
      { DRY_RUN: "false" },
    );
    expect(m.closed.some((c) => c.pull_number === 281)).toBe(true);
    expect(m.closed.some((c) => c.pull_number === 282)).toBe(false);
    expect(m.unassigned).toHaveLength(0);
    expect(m.comments.find((c) => c.number === 281).body).toContain("remain assigned");
  });

  test("both linked PRs stale -> close both + unassign", async () => {
    const m = await run(
      specWithPRs(119, "alice", [
        { num: 291, author: "alice", reviews: [humanReview(70)], commitDate: daysAgo(80) },
        { num: 292, author: "alice", reviews: [humanReview(65)], commitDate: daysAgo(70) },
      ]),
      { DRY_RUN: "false" },
    );
    expect(m.closed.some((c) => c.pull_number === 291)).toBe(true);
    expect(m.closed.some((c) => c.pull_number === 292)).toBe(true);
    expect(unassignedFrom(m, 119, "alice")).toBe(true);
    expect(m.comments.find((c) => c.number === 291).body).toContain("unassigning you");
  });

  test("stale PR + remind-stage PR -> close + remind, keep assignment", async () => {
    const m = await run(
      specWithPRs(120, "alice", [
        { num: 301, author: "alice", reviews: [humanReview(70)], commitDate: daysAgo(80) },
        { num: 302, author: "alice", reviews: [humanReview(15)], commitDate: daysAgo(20) },
      ]),
      { DRY_RUN: "false" },
    );
    expect(m.closed.some((c) => c.pull_number === 301)).toBe(true);
    expect(commentedOn(m, 302, "<!-- pr-inactivity-bot-marker -->")).toBe(true);
    expect(m.unassigned).toHaveLength(0);
  });

  test("future-dated head commit is ignored -> staleness falls back to review date", async () => {
    const m = await run(specWithPR(121, 321, "alice", { author: "alice", reviews: [humanReview(70)], commitDate: daysAgo(-30) }), {
      DRY_RUN: "false",
    });
    expect(m.closed.some((c) => c.pull_number === 321)).toBe(true);
  });
});
