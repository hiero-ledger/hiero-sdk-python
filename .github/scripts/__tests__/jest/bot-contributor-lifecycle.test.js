// SPDX-License-Identifier: Apache-2.0

/**
 * @fileoverview
 * Unit tests for bot-contributor-lifecycle.js. Runs the real handler against a
 * fake octokit-shaped `github` client with in-memory fixtures and asserts which
 * mutations (comments / unassign / close) would happen.
 */

const fs = require("fs");
const os = require("os");
const path = require("path");

const bot = require("../../bot-contributor-lifecycle.js");

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
    failUnassignFor = [], // logins whose removeAssignees call should throw
    failCommentOn = [], // issue/PR numbers whose createComment call should throw
    failCloseFor = [], // PR numbers whose pulls.update (close) call should throw
  } = spec;

  const github = {
    paginate: async (fn, opts) => fn(opts),
    graphql: async (_query, vars) => graphqlByIssue[vars.number] || { repository: { issue: {} } },
    rest: {
      issues: {
        listForRepo: () => issues,
        listComments: ({ issue_number }) => commentsByIssue[issue_number] || [],
        createComment: async ({ issue_number, body }) => {
          if (failCommentOn.includes(issue_number)) {
            throw new Error(`createComment failed for #${issue_number}`);
          }
          mut.comments.push({ number: issue_number, body });
        },
        removeAssignees: async ({ issue_number, assignees }) => {
          if (assignees.some((a) => failUnassignFor.includes(a))) {
            throw new Error(`removeAssignees failed for ${assignees.join(",")}`);
          }
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
          if (failCloseFor.includes(pull_number)) {
            throw new Error(`pulls.update failed for #${pull_number}`);
          }
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

// prNumbers: linked (closing) PRs. mentionPrNumbers: bare cross-references that do
// NOT close the issue (willCloseTarget=false) and must not count as a linked PR.
function gqlIssue({ assignedEvents = [], prNumbers = [], mentionPrNumbers = [] }) {
  const crossRefNode = (n, willCloseTarget) => ({
    willCloseTarget,
    source: { number: n, state: "OPEN", repository: { nameWithOwner: "o/r" } },
  });
  return {
    repository: {
      issue: {
        assignedEvents: { nodes: assignedEvents },
        crossRefs: {
          nodes: [
            ...prNumbers.map((n) => crossRefNode(n, true)),
            ...mentionPrNumbers.map((n) => crossRefNode(n, false)),
          ],
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

// GITHUB_STEP_SUMMARY is cleared too: CI sets it for real, and the bot under test
// must not append to the actual workflow summary during unit runs.
const THRESHOLD_KEYS = ["DRY_RUN", "ISSUE_REMIND_DAYS", "ISSUE_UNASSIGN_DAYS", "PR_REMIND_DAYS", "PR_CLOSE_DAYS", "SKIP_PR_LABELS", "GITHUB_STEP_SUMMARY"];

async function run(spec, env = {}, { expectThrow = false } = {}) {
  // Snapshot the keys we touch and restore them afterwards so we never pollute
  // process.env for other test files / cases.
  const saved = {};
  for (const k of THRESHOLD_KEYS) {
    saved[k] = process.env[k];
    delete process.env[k];
  }
  Object.assign(process.env, env);
  const { github, context, mut } = makeEnv(spec);
  const spy = jest.spyOn(console, "log").mockImplementation(() => {});
  try {
    await bot({ github, context });
  } catch (err) {
    // The bot fails loudly when any issue errors (stats.errors > 0). Tests that
    // exercise that path opt in via expectThrow so they can still inspect `mut`;
    // otherwise an unexpected throw propagates and fails the test.
    if (!expectThrow) throw err;
    mut.threw = err;
  } finally {
    spy.mockRestore();
    for (const k of THRESHOLD_KEYS) {
      if (saved[k] === undefined) delete process.env[k];
      else process.env[k] = saved[k];
    }
  }
  return mut;
}

const commentedOn = (mut, number, marker) =>
  mut.comments.some((c) => c.number === number && (!marker || c.body.includes(marker)));
const unassignedFrom = (mut, issue, login) =>
  mut.unassigned.some((u) => u.issue_number === issue && u.assignees.includes(login));

describe("bot-contributor-lifecycle", () => {
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

  test("a non-bot user's hidden marker does NOT suppress the reminder", async () => {
    const m = await run(
      specNoPR(122, "alice", 10, [
        { user: { login: "alice", type: "User" }, body: "<!-- issue-reminder-bot --> sneaky", created_at: daysAgo(1) },
      ]),
      { DRY_RUN: "false" },
    );
    expect(commentedOn(m, 122, "<!-- issue-reminder-bot -->")).toBe(true);
    expect(m.comments.filter((c) => c.number === 122)).toHaveLength(1);
  });

  test("malformed threshold falls back to the default (no premature unassign)", async () => {
    const m = await run(specNoPR(123, "alice", 10), { DRY_RUN: "false", ISSUE_UNASSIGN_DAYS: "0oops" });
    expect(m.unassigned).toHaveLength(0); // falls back to 21 -> 10d only triggers a reminder
    expect(commentedOn(m, 123, "<!-- issue-reminder-bot -->")).toBe(true);
  });

  test("collaborative co-assignment: a teammate's /working keeps the shared PR alive", async () => {
    // Issue assigned to alice + bob; the linked PR is the team's shared work. bob's /working
    // counts for the PR even though alice opened it — a PR by one counts for both.
    const spec = specWithPR(125, 251, ["alice", "bob"], { author: "alice", reviews: [humanReview(70)], commitDate: daysAgo(80) });
    spec.commentsByIssue[125] = [{ user: { login: "bob", type: "User" }, body: "/working", created_at: daysAgo(2) }];
    const m = await run(spec, { DRY_RUN: "false" });
    expect(m.closed).toHaveLength(0); // shared PR kept alive by bob's /working
    expect(m.unassigned).toHaveLength(0); // neither teammate unassigned
  });

  test("missing assignment event -> reminder via created_at, never unassign", async () => {
    const spec = {
      issues: [{ number: 126, assignees: [{ login: "alice" }], created_at: daysAgo(30) }],
      commentsByIssue: { 126: [] },
      graphqlByIssue: { 126: gqlIssue({ assignedEvents: [], prNumbers: [] }) },
    };
    const m = await run(spec, { DRY_RUN: "false" });
    expect(m.unassigned).toHaveLength(0); // no real assignment date -> never unassign
    expect(commentedOn(m, 126, "<!-- issue-reminder-bot -->")).toBe(true); // but still nudges (created 30d ago)
  });

  test("a bare mention (willCloseTarget=false) is NOT a linked PR -> stale assignee is unassigned", async () => {
    // An unrelated open PR merely cross-references the issue without a closing keyword.
    // It must not exempt the idle assignee from the no-PR escalation.
    const spec = {
      issues: [{ number: 127, assignees: [{ login: "alice" }] }],
      commentsByIssue: { 127: [] },
      graphqlByIssue: {
        127: gqlIssue({
          assignedEvents: [{ createdAt: daysAgo(30), assignee: { login: "alice" } }],
          mentionPrNumbers: [427],
        }),
      },
    };
    const m = await run(spec, { DRY_RUN: "false" });
    expect(unassignedFrom(m, 127, "alice")).toBe(true);
    expect(commentedOn(m, 127, "<!-- inactivity-unassign:alice -->")).toBe(true);
  });

  test("one assignee's unassign failure does not block the other (per-assignee isolation)", async () => {
    const spec = { ...specNoPR(128, ["alice", "bob"], 30), failUnassignFor: ["alice"] };
    const m = await run(spec, { DRY_RUN: "false" }, { expectThrow: true });
    expect(m.threw).toBeDefined(); // run still fails loudly so the failure is visible
    expect(unassignedFrom(m, 128, "alice")).toBe(false); // alice's removal threw
    expect(unassignedFrom(m, 128, "bob")).toBe(true); // ...but bob is still processed
  });

  test("recently co-assigned teammate is spared when a stale PR closes", async () => {
    // alice's PR went stale (70d); bob was co-assigned 2 days ago. The PR still closes,
    // alice is unassigned, but bob keeps his fresh assignment.
    const spec = specWithPR(129, 261, ["alice", "bob"], { author: "alice", reviews: [humanReview(70)], commitDate: daysAgo(80) });
    spec.graphqlByIssue[129] = gqlIssue({
      assignedEvents: [
        { createdAt: daysAgo(120), assignee: { login: "alice" } },
        { createdAt: daysAgo(2), assignee: { login: "bob" } },
      ],
      prNumbers: [261],
    });
    const m = await run(spec, { DRY_RUN: "false" });
    expect(m.closed.some((c) => c.pull_number === 261)).toBe(true);
    expect(unassignedFrom(m, 129, "alice")).toBe(true);
    expect(unassignedFrom(m, 129, "bob")).toBe(false);
    const closeComment = m.comments.find((c) => c.number === 261);
    expect(closeComment.body).toContain("unassigning @alice");
    expect(closeComment.body).toContain("recently-assigned contributors remain assigned");
  });

  test("PR-stage unassign failure does not block the other assignee", async () => {
    const spec = {
      ...specWithPR(130, 262, ["alice", "bob"], { author: "alice", reviews: [humanReview(70)], commitDate: daysAgo(80) }),
      failUnassignFor: ["alice"],
    };
    const m = await run(spec, { DRY_RUN: "false" }, { expectThrow: true });
    expect(m.threw).toBeDefined(); // still fails loudly at the end
    expect(m.closed.some((c) => c.pull_number === 262)).toBe(true); // close already happened
    expect(unassignedFrom(m, 130, "alice")).toBe(false); // alice's removal threw
    expect(unassignedFrom(m, 130, "bob")).toBe(true); // ...but bob is still processed
  });

  test("reminder marker from a PREVIOUS assignment cycle does not suppress a new reminder", async () => {
    // alice was reminded 20d ago (previous cycle), then re-assigned 10d ago and idled again.
    const m = await run(
      specNoPR(131, "alice", 10, [
        { user: { login: "github-actions[bot]" }, body: "<!-- issue-reminder-bot -->\nold cycle", created_at: daysAgo(20) },
      ]),
      { DRY_RUN: "false" },
    );
    expect(commentedOn(m, 131, "<!-- issue-reminder-bot -->")).toBe(true);
  });

  test("unassign marker from a PREVIOUS cycle -> fresh comment before unassigning again", async () => {
    // alice was unassigned 40d ago, re-assigned 30d ago, idled again: she must get a NEW
    // notice, not a silent removal suppressed by the stale marker.
    const m = await run(
      specNoPR(132, "alice", 30, [
        { user: { login: "github-actions[bot]" }, body: "<!-- inactivity-unassign:alice -->\nold cycle", created_at: daysAgo(40) },
      ]),
      { DRY_RUN: "false" },
    );
    expect(commentedOn(m, 132, "<!-- inactivity-unassign:alice -->")).toBe(true);
    expect(unassignedFrom(m, 132, "alice")).toBe(true);
  });

  test("PR reminder is re-issued for a NEW inactivity cycle", async () => {
    // Reminder posted 30d ago; the author then pushed (20d ago) and a review landed (15d
    // ago); now idle past the remind threshold again -> the old marker is stale.
    const m = await run(
      specWithPR(133, 263, "alice", {
        author: "alice",
        reviews: [humanReview(15)],
        commitDate: daysAgo(20),
        prComments: [{ user: { login: "github-actions[bot]" }, body: "<!-- pr-inactivity-bot-marker -->\nold cycle", created_at: daysAgo(30) }],
      }),
      { DRY_RUN: "false" },
    );
    expect(commentedOn(m, 263, "<!-- pr-inactivity-bot-marker -->")).toBe(true);
  });

  test("one PR's close failure does not block the other close or the unassign", async () => {
    const spec = {
      ...specWithPRs(134, "alice", [
        { num: 264, author: "alice", reviews: [humanReview(70)], commitDate: daysAgo(80) },
        { num: 265, author: "alice", reviews: [humanReview(70)], commitDate: daysAgo(80) },
      ]),
      failCloseFor: [264],
    };
    const m = await run(spec, { DRY_RUN: "false" }, { expectThrow: true });
    expect(m.threw).toBeDefined(); // still fails loudly at the end
    expect(m.closed.some((c) => c.pull_number === 265)).toBe(true); // second close proceeds
    expect(unassignedFrom(m, 134, "alice")).toBe(true); // unassign still happens
  });

  test("a failed close comment still lets the unassign proceed (reliability guarantee)", async () => {
    const spec = {
      ...specWithPR(135, 266, "alice", { author: "alice", reviews: [humanReview(70)], commitDate: daysAgo(80) }),
      failCommentOn: [266],
    };
    const m = await run(spec, { DRY_RUN: "false" }, { expectThrow: true });
    expect(m.threw).toBeDefined();
    expect(m.closed).toHaveLength(0); // this PR's close is retried next run (marker-safe)
    expect(unassignedFrom(m, 135, "alice")).toBe(true); // the important action still happens
  });

  test("one PR's reminder failure does not block the other reminder", async () => {
    const spec = {
      ...specWithPRs(136, "alice", [
        { num: 268, author: "alice", reviews: [humanReview(15)], commitDate: daysAgo(20) },
        { num: 269, author: "alice", reviews: [humanReview(15)], commitDate: daysAgo(20) },
      ]),
      failCommentOn: [268],
    };
    const m = await run(spec, { DRY_RUN: "false" }, { expectThrow: true });
    expect(m.threw).toBeDefined();
    expect(commentedOn(m, 269, "<!-- pr-inactivity-bot-marker -->")).toBe(true); // second reminder proceeds
  });

  test("writes a markdown stats table to GITHUB_STEP_SUMMARY when set", async () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "lifecycle-summary-"));
    const summaryFile = path.join(dir, "summary.md");
    try {
      const m = await run(specNoPR(137, "alice", 10), { DRY_RUN: "false", GITHUB_STEP_SUMMARY: summaryFile });
      expect(commentedOn(m, 137, "<!-- issue-reminder-bot -->")).toBe(true);

      const summary = fs.readFileSync(summaryFile, "utf8");
      expect(summary).toContain("Contributor Lifecycle Bot");
      expect(summary).toContain("| Issue reminders | 1 |");
      expect(summary).toContain("| Errors | 0 |");
    } finally {
      fs.rmSync(dir, { recursive: true, force: true });
    }
  });
});
