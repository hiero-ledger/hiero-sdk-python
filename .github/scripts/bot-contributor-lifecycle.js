/*
------------------------------------------------------------------------------
Contributor Lifecycle Bot

Runs on a schedule via actions/github-script. Scans every OPEN issue that has
assignees (not PRs). For each issue it applies a staged escalation:

  Issue has NO linked open PR (evaluated per assignee):
    age >= ISSUE_UNASSIGN_DAYS  -> comment + unassign that assignee
    age >= ISSUE_REMIND_DAYS    -> one reminder comment mentioning all assignees
                                   in the remind window (marker-guarded)
    else                        -> keep

  Issue HAS linked open PR(s) (evaluated once per PR for the whole issue):
    PR not open                 -> skip
    PR has a skip label         -> skip   (configurable, see SKIP_PR_LABELS)
    no human review             -> keep    (never close an un-reviewed PR)
    reviewed, age >= PR_CLOSE_DAYS  -> comment + close PR + unassign ALL assignees
    reviewed, age >= PR_REMIND_DAYS -> reminder on PR (marker-guarded)
    else                        -> keep

"age" is measured from the most recent activity, which always includes a recent
`/working` comment from an assignee — so `/working` resets every timer. PR age
also includes the last commit and the last human (non-bot, non-author) review.

DRY_RUN=true logs intended actions and mutates nothing.

Config (env, all override-able via the workflow's "Run workflow" inputs):
  ISSUE_REMIND_DAYS=7  ISSUE_UNASSIGN_DAYS=21  PR_REMIND_DAYS=10  PR_CLOSE_DAYS=60
  SKIP_PR_LABELS="status: discussion"   comma-separated; a linked PR carrying any
                                        of these labels is never reminded or closed
------------------------------------------------------------------------------
*/

const DAY_MS = 24 * 60 * 60 * 1000;

// HTML markers — issues/PRs already pinged are not re-pinged.
const MARK_ISSUE_REMIND = "<!-- issue-reminder-bot -->";
const MARK_PR_REMIND = "<!-- pr-inactivity-bot-marker -->";
const MARK_CLOSE = "<!-- inactivity-close-bot -->";
const unassignMarkerFor = (login) => `<!-- inactivity-unassign:${login} -->`;

const WORKING_RE = /(^|\s)\/working(\s|$)/i;

// Default set of PR labels that exempt a PR from reminder/close. Override with the
// SKIP_PR_LABELS env var (comma-separated). Matched case-insensitively.
const DEFAULT_SKIP_PR_LABELS = "status: discussion";

const DISCORD_LINK =
  "[Discord](https://github.com/hiero-ledger/sdk-collaboration-hub/blob/main/guides/issue-progression/for-developers/discord.md)";
const OFFICE_HOURS =
  "[Office Hours](https://zoom-lfx.platform.linuxfoundation.org/meetings/hiero?view=week)";

// ---- small pure helpers ----

function intEnv(name, def) {
  const raw = process.env[name];
  if (raw === undefined || raw === null || raw === "") return def;
  const trimmed = String(raw).trim();
  // Strict: only a complete non-negative integer. Reject things like "10 days" or
  // "0oops" that parseInt would silently coerce into a (possibly destructive) threshold.
  if (!/^\d+$/.test(trimmed)) {
    console.log(`  [WARN] ${name}="${raw}" is not a non-negative integer; using default ${def}`);
    return def;
  }
  return parseInt(trimmed, 10);
}

function parseSkipLabels(raw) {
  return (raw === undefined || raw === null || raw === "" ? DEFAULT_SKIP_PR_LABELS : raw)
    .split(",")
    .map((s) => s.trim().toLowerCase())
    .filter(Boolean);
}

function readConfig() {
  return {
    issueRemindDays: intEnv("ISSUE_REMIND_DAYS", 7),
    issueUnassignDays: intEnv("ISSUE_UNASSIGN_DAYS", 21),
    prRemindDays: intEnv("PR_REMIND_DAYS", 10),
    prCloseDays: intEnv("PR_CLOSE_DAYS", 60),
    skipPrLabels: parseSkipLabels(process.env.SKIP_PR_LABELS),
    dryRun: (process.env.DRY_RUN || "false").toString().toLowerCase() === "true",
  };
}

function daysSince(date, nowMs) {
  return Math.floor((nowMs - date.getTime()) / DAY_MS);
}

function maxDate(dates) {
  const valid = dates.filter(Boolean);
  if (valid.length === 0) return null;
  return new Date(Math.max(...valid.map((d) => d.getTime())));
}

// A comment authored by a GitHub App / Actions bot (login ends in "[bot]" — a suffix
// users cannot have, since "[" and "]" are not valid login characters).
function isBotAuthored(comment) {
  const login = comment?.user?.login || "";
  return comment?.user?.type === "Bot" || login.endsWith("[bot]");
}

// Only honour markers we posted ourselves, so a non-bot user can't suppress lifecycle
// actions by pasting a hidden marker comment.
function hasMarker(comments, marker) {
  return comments.some(
    (c) => isBotAuthored(c) && typeof c.body === "string" && c.body.includes(marker),
  );
}

function mentions(logins) {
  return logins.map((l) => `@${l}`).join(", ");
}

// Latest `/working` comment from any of the given users (Date or null).
function latestWorkingAmong(comments, logins) {
  const set = new Set(logins);
  let latest = null;
  for (const c of comments) {
    if (!set.has(c?.user?.login)) continue;
    if (typeof c.body !== "string" || !WORKING_RE.test(c.body)) continue;
    const d = new Date(c.created_at);
    if (!latest || d > latest) latest = d;
  }
  return latest;
}

// Most recent ASSIGNED_EVENT for this assignee, from the issue GraphQL payload.
function assignmentDateFor(graph, assignee) {
  const nodes = graph?.repository?.issue?.assignedEvents?.nodes || [];
  let latest = null;
  for (const n of nodes) {
    if (n?.assignee?.login === assignee && n.createdAt) {
      const d = new Date(n.createdAt);
      if (!latest || d > latest) latest = d;
    }
  }
  return latest;
}

// Open PRs in THIS repo that actually LINK this issue — combining closedBy
// references with cross-references that will close the issue. A bare mention
// (e.g. "see also #123" with no closing keyword / dev-link) is NOT a link: it
// must not block unassignment, or an unrelated PR could exempt an idle assignee
// forever. willCloseTarget is GitHub's own signal that the source PR closes this
// issue, so it's the same notion of "linked" as closedByPullRequestsReferences.
function linkedOpenPRNumbers(graph, nameWithOwner) {
  const issue = graph?.repository?.issue;
  const set = new Set();
  for (const n of issue?.closedByPullRequestsReferences?.nodes || []) {
    if (n?.state === "OPEN" && n?.repository?.nameWithOwner === nameWithOwner && n.number) {
      set.add(n.number);
    }
  }
  for (const n of issue?.crossRefs?.nodes || []) {
    if (!n?.willCloseTarget) continue; // mere mention, not a closing link — ignore
    const s = n.source;
    if (s?.state === "OPEN" && s?.repository?.nameWithOwner === nameWithOwner && s.number) {
      set.add(s.number);
    }
  }
  return [...set];
}

// First skip label found on the PR (string) or null.
function prSkipLabel(pr, skipLabels) {
  for (const l of pr.labels || []) {
    const name = (l.name || "").trim().toLowerCase();
    if (skipLabels.includes(name)) return name;
  }
  return null;
}

// ---- I/O helpers (octokit) ----

async function listIssueComments(github, owner, repo, number) {
  return github.paginate(github.rest.issues.listComments, {
    owner,
    repo,
    issue_number: number,
    per_page: 100,
  });
}

async function fetchIssueGraph(github, owner, repo, number) {
  // crossRefs uses last:100 to bias toward the most RECENT cross-references, so a
  // recently-opened linking PR isn't missed on a heavily-referenced issue.
  const query = `
    query($owner:String!, $repo:String!, $number:Int!) {
      repository(owner:$owner, name:$repo) {
        issue(number:$number) {
          assignedEvents: timelineItems(itemTypes:[ASSIGNED_EVENT], last:100) {
            nodes { ... on AssignedEvent { createdAt assignee { ... on User { login } } } }
          }
          crossRefs: timelineItems(itemTypes:[CROSS_REFERENCED_EVENT], last:100) {
            nodes {
              ... on CrossReferencedEvent {
                willCloseTarget
                source { ... on PullRequest { number state repository { nameWithOwner } } }
              }
            }
          }
          closedByPullRequestsReferences(first:50, includeClosedPrs:false) {
            nodes { number state repository { nameWithOwner } }
          }
        }
      }
    }`;
  return github.graphql(query, { owner, repo, number });
}

// Latest human (non-bot, non-author) review date for a PR (Date or null).
async function lastHumanReviewDate(github, owner, repo, prNumber, prAuthor) {
  const reviews = await github.paginate(github.rest.pulls.listReviews, {
    owner,
    repo,
    pull_number: prNumber,
    per_page: 100,
  });
  let latest = null;
  for (const r of reviews) {
    if (!r.user || isBotAuthored(r)) continue;
    if (r.user.login === prAuthor) continue;
    if (!r.submitted_at) continue;
    const d = new Date(r.submitted_at);
    if (!latest || d > latest) latest = d;
  }
  return latest;
}

// Last commit date on the PR head (Date or null on failure).
async function lastCommitDate(github, pr) {
  const headOwner = pr.head?.repo?.owner?.login || pr.base?.repo?.owner?.login;
  const headRepo = pr.head?.repo?.name || pr.base?.repo?.name;
  if (!headOwner || !headRepo || !pr.head?.sha) return null;
  try {
    const res = await github.rest.repos.getCommit({
      owner: headOwner,
      repo: headRepo,
      ref: pr.head.sha,
    });
    const commit = res.data?.commit ?? null;
    const d = new Date(commit?.committer?.date || commit?.author?.date || pr.created_at);
    // Commit dates are author-controlled; ignore implausibly future-dated commits so a
    // PR can't dodge the inactivity clock with a forged committer date. Falls back to the
    // (server-set) review/working timestamps instead.
    if (d.getTime() > Date.now() + DAY_MS) {
      console.log(`  [WARN] PR #${pr.number} head commit date is in the future; ignoring`);
      return null;
    }
    return d;
  } catch (err) {
    console.log(`  [WARN] Could not fetch head commit for PR #${pr.number}:`, err.message || err);
    return null;
  }
}

// ---- message builders ----

function issueReminderBody(assignees) {
  return `${MARK_ISSUE_REMIND}
Hi ${mentions(assignees)} 👋

This issue has been assigned but no pull request has been created yet.
Are you still planning on working on it?
If you are, please create a draft PR linked to this issue or comment \`/working\` to let us know.
If you're no longer able to work on this issue, you can comment \`/unassign\` to release it.

From the Python SDK Team`;
}

function issueUnassignBody(assignee, ageDays) {
  return `${unassignMarkerFor(assignee)}
Hi @${assignee}, this is CronInactivityBot 👋

You were assigned to this issue **${ageDays} days** ago, and there is currently no open pull request linked to it.
To keep the backlog available for active contributors, I'm unassigning you for now.

If you're no longer interested, no action is needed.

**Tip:** You can comment \`/unassign\` on any issue to proactively step away before this bot kicks in.

If you'd like to continue working on this later, feel free to comment \`/assign\` on the issue to get re-assigned, and open a new PR when you're ready. 🚀`;
}

function prReminderBody(prAuthor, ageDays) {
  return `${MARK_PR_REMIND}
Hi @${prAuthor},

This pull request has had no activity for ${ageDays} days. Are you still working on it?
To keep the PR active, you can:

- Push a new commit.
- Comment \`/working\` on the linked **issue** (not this PR).

If you're no longer working on this, please comment \`/unassign\` on the linked issue to release it for others. Otherwise, this PR may be closed due to inactivity.

Reach out on discord or join our office hours if you need assistance.

- ${DISCORD_LINK}
- ${OFFICE_HOURS}

From the Python SDK Team`;
}

function prCloseBody(assignees, ageDays, willUnassign) {
  const tail = willUnassign
    ? "so I'm closing it and unassigning you from the linked issue to keep the backlog healthy."
    : "so I'm closing it to keep the backlog healthy. Another open pull request is still linked to the issue, so you remain assigned.";
  return `${MARK_CLOSE}
Hi ${mentions(assignees)}, this is CronInactivityBot 👋

This pull request has been reviewed but has had no new activity for **${ageDays} days**, ${tail}

If you're no longer interested, no action is needed.

**Tip:** You can comment \`/unassign\` on any issue to proactively step away before this bot kicks in.

If you'd like to continue working on this later, feel free to comment \`/assign\` on the issue to get re-assigned, and open a new PR when you're ready. 🚀`;
}

// ---- mutating actions (dry-run aware) ----

async function postComment(github, owner, repo, number, body, cfg) {
  if (cfg.dryRun) {
    console.log(`    [DRY RUN] Would comment on #${number}`);
    return;
  }
  await github.rest.issues.createComment({ owner, repo, issue_number: number, body });
  console.log(`    [ACTION] Commented on #${number}`);
}

async function removeAssignee(github, owner, repo, issueNumber, assignee, cfg) {
  if (cfg.dryRun) {
    console.log(`    [DRY RUN] Would unassign @${assignee} from issue #${issueNumber}`);
    return;
  }
  await github.rest.issues.removeAssignees({
    owner,
    repo,
    issue_number: issueNumber,
    assignees: [assignee],
  });
  console.log(`    [ACTION] Unassigned @${assignee} from issue #${issueNumber}`);
}

async function closePR(github, owner, repo, prNumber, cfg) {
  if (cfg.dryRun) {
    console.log(`    [DRY RUN] Would close PR #${prNumber}`);
    return;
  }
  await github.rest.pulls.update({ owner, repo, pull_number: prNumber, state: "closed" });
  console.log(`    [ACTION] Closed PR #${prNumber}`);
}

// ---- stage handlers ----

async function handleNoPRStage(github, owner, repo, issue, graph, comments, nowMs, cfg, stats) {
  const toUnassign = [];
  const toRemind = [];

  for (const assignee of issue.assignees.map((a) => a.login)) {
    let assignedAt = assignmentDateFor(graph, assignee);
    let canUnassign = true;
    if (!assignedAt) {
      // No assignment event in the timeline (rare — e.g. a timeline gap). Fall back to the
      // issue's creation date so we can still nudge, but never unassign without a real
      // assignment timestamp (created_at could be far older than the actual assignment).
      assignedAt = issue.created_at ? new Date(issue.created_at) : null;
      canUnassign = false;
      stats.skipNoAssignEvent++;
      console.log(`    [WARN] @${assignee}: no assignment event; using issue.created_at for reminder only (won't unassign)`);
      if (!assignedAt) {
        console.log(`    [SKIP] @${assignee}: no assignment event and no created_at`);
        continue;
      }
    }
    const baseline = maxDate([assignedAt, latestWorkingAmong(comments, [assignee])]);
    const ageDays = daysSince(baseline, nowMs);
    if (canUnassign && ageDays >= cfg.issueUnassignDays) {
      toUnassign.push({ assignee, ageDays });
    } else if (ageDays >= cfg.issueRemindDays) {
      toRemind.push({ assignee, ageDays });
    } else {
      console.log(`    [KEEP] @${assignee}: fresh (~${ageDays}d < ${cfg.issueRemindDays}d)`);
    }
  }

  // Unassign each stale assignee individually (their dates differ). The personalized
  // comment is guarded by a per-user marker so a failed removal won't re-comment.
  // Isolate each assignee in its own try/catch: one failed removal must not block the
  // other assignees' actions (or the reminder below). The error is still counted so the
  // run fails loudly at the end; the marker guard makes the next run's retry safe.
  for (const { assignee, ageDays } of toUnassign) {
    try {
      console.log(`    [RESULT] @${assignee}: stale (~${ageDays}d >= ${cfg.issueUnassignDays}d, no PR) -> unassign`);
      if (!hasMarker(comments, unassignMarkerFor(assignee))) {
        await postComment(github, owner, repo, issue.number, issueUnassignBody(assignee, ageDays), cfg);
      }
      await removeAssignee(github, owner, repo, issue.number, assignee, cfg);
      stats.unassigned++;
    } catch (err) {
      console.log(`    [ERROR] @${assignee}: unassign failed:`, err.message || err);
      stats.errors++;
    }
  }

  // Remind everyone in the remind window with a single comment (marker-guarded).
  if (toRemind.length > 0) {
    if (hasMarker(comments, MARK_ISSUE_REMIND)) {
      console.log(`    [SKIP] reminder already posted on issue #${issue.number}`);
    } else {
      const who = toRemind.map((r) => r.assignee);
      console.log(`    [RESULT] idle (no PR) -> remind ${mentions(who)}`);
      await postComment(github, owner, repo, issue.number, issueReminderBody(who), cfg);
      stats.issueReminders++;
    }
  }
}

async function handlePRStage(github, owner, repo, issue, prNumbers, comments, nowMs, cfg, stats) {
  const assignees = issue.assignees.map((a) => a.login);
  // Co-assignment is collaborative: a linked PR is the team's shared work, so a /working
  // from ANY assignee keeps every linked PR alive (a PR by one counts for both). This is
  // intentional — do not scope /working to individual PR authors.
  const workingAt = latestWorkingAmong(comments, assignees);

  // Pass 1 — classify each linked PR without mutating anything.
  const toClose = [];
  const toRemind = [];
  // An open linked PR that still represents active/blocked work, so the assignment is kept.
  let survivingOpenPR = false;

  for (const prNum of prNumbers) {
    let pr;
    try {
      pr = (await github.rest.pulls.get({ owner, repo, pull_number: prNum })).data;
    } catch (err) {
      console.log(`    [SKIP] PR #${prNum}: fetch failed:`, err.message || err);
      survivingOpenPR = true; // unknown — be conservative, don't unassign
      continue;
    }
    if (pr.state !== "open") {
      console.log(`    [SKIP] PR #${prNum} is ${pr.state}`);
      continue;
    }
    const skipLabel = prSkipLabel(pr, cfg.skipPrLabels);
    if (skipLabel) {
      console.log(`    [SKIP] PR #${prNum} has skip label '${skipLabel}'`);
      stats.skipLabel++;
      survivingOpenPR = true;
      continue;
    }
    const reviewDate = await lastHumanReviewDate(github, owner, repo, prNum, pr.user?.login);
    if (!reviewDate) {
      console.log(`    [KEEP] PR #${prNum} has no human review yet`);
      stats.skipNoReview++;
      survivingOpenPR = true;
      continue;
    }
    const commitDate = await lastCommitDate(github, pr);
    const ageDays = daysSince(maxDate([reviewDate, commitDate, workingAt]), nowMs);
    console.log(`    [INFO] PR #${prNum} reviewed; last activity ~${ageDays}d ago`);

    // Close takes priority over remind so an (unusual) close < remind config still closes.
    if (ageDays >= cfg.prCloseDays) {
      toClose.push({ prNum, ageDays });
    } else if (ageDays >= cfg.prRemindDays) {
      toRemind.push({ prNum, author: pr.user?.login, ageDays });
      survivingOpenPR = true; // reminded PR stays open
    } else {
      console.log(`    [KEEP] PR #${prNum} active (< ${Math.min(cfg.prRemindDays, cfg.prCloseDays)}d)`);
      survivingOpenPR = true;
    }
  }

  // Only unassign when we're closing at least one PR AND nothing else keeps the issue open.
  const willUnassign = toClose.length > 0 && !survivingOpenPR;

  // Pass 2 — close stale PRs (marker-guarded comment, then close).
  for (const { prNum, ageDays } of toClose) {
    let prComments = [];
    try {
      prComments = await listIssueComments(github, owner, repo, prNum);
    } catch (err) {
      console.log(`    [WARN] PR #${prNum}: could not list comments (close note may duplicate):`, err.message || err);
    }
    console.log(`    [RESULT] PR #${prNum} stale (>= ${cfg.prCloseDays}d) -> close${willUnassign ? " + unassign" : " (keep assignees)"}`);
    if (!hasMarker(prComments, MARK_CLOSE)) {
      await postComment(github, owner, repo, prNum, prCloseBody(assignees, ageDays, willUnassign), cfg);
    }
    await closePR(github, owner, repo, prNum, cfg);
    stats.closed++;
  }

  // Pass 2 — remind on inactive (but not yet closeable) PRs.
  for (const { prNum, author, ageDays } of toRemind) {
    let prComments;
    try {
      prComments = await listIssueComments(github, owner, repo, prNum);
    } catch (err) {
      console.log(`    [SKIP] PR #${prNum}: could not list comments (avoid duplicate):`, err.message || err);
      continue;
    }
    if (hasMarker(prComments, MARK_PR_REMIND)) {
      console.log(`    [SKIP] PR #${prNum} already has an inactivity reminder`);
      continue;
    }
    console.log(`    [RESULT] PR #${prNum} inactive (>= ${cfg.prRemindDays}d) -> remind`);
    await postComment(github, owner, repo, prNum, prReminderBody(author || assignees[0], ageDays), cfg);
    stats.prReminders++;
  }

  // Unassign every assignee once, only when warranted.
  if (willUnassign) {
    for (const assignee of assignees) {
      await removeAssignee(github, owner, repo, issue.number, assignee, cfg);
      stats.unassigned++;
    }
  } else if (toClose.length > 0) {
    console.log(`    [INFO] Closed stale PR(s) but another linked PR is still open -> keeping assignees`);
  }
}

// ---- entry point ----

module.exports = async ({ github, context }) => {
  const { owner, repo } = context.repo;
  const nameWithOwner = `${owner}/${repo}`;
  const cfg = readConfig();
  const nowMs = Date.now();

  console.log("------------------------------------------------------------");
  console.log(" Contributor Lifecycle Bot");
  console.log(`  Repo: ${nameWithOwner}`);
  console.log(`  Thresholds: issue remind ${cfg.issueRemindDays}d / unassign ${cfg.issueUnassignDays}d`);
  console.log(`              PR remind ${cfg.prRemindDays}d / close ${cfg.prCloseDays}d`);
  console.log(`  Skip PR labels: ${cfg.skipPrLabels.map((l) => `'${l}'`).join(", ") || "(none)"}`);
  console.log(`  Dry run: ${cfg.dryRun}`);
  console.log("------------------------------------------------------------");

  const stats = {
    scanned: 0,
    issueReminders: 0,
    prReminders: 0,
    unassigned: 0,
    closed: 0,
    skipLabel: 0,
    skipNoReview: 0,
    skipNoAssignEvent: 0,
    errors: 0,
  };

  const issues = await github.paginate(github.rest.issues.listForRepo, {
    owner,
    repo,
    state: "open",
    per_page: 100,
  });

  for (const issue of issues) {
    if (issue.pull_request) continue; // skip PRs
    if (!issue.assignees || issue.assignees.length === 0) continue;
    stats.scanned++;

    console.log(`\n== ISSUE #${issue.number} (assignees: ${mentions(issue.assignees.map((a) => a.login))}) ==`);

    try {
      const comments = await listIssueComments(github, owner, repo, issue.number);
      const graph = await fetchIssueGraph(github, owner, repo, issue.number);
      const prNumbers = linkedOpenPRNumbers(graph, nameWithOwner);

      if (prNumbers.length === 0) {
        await handleNoPRStage(github, owner, repo, issue, graph, comments, nowMs, cfg, stats);
      } else {
        console.log(`    [INFO] Linked open PRs: ${prNumbers.join(", ")}`);
        await handlePRStage(github, owner, repo, issue, prNumbers, comments, nowMs, cfg, stats);
      }
    } catch (err) {
      console.log(`  [ERROR] Issue #${issue.number} failed:`, err.message || err);
      stats.errors++;
    }
  }

  console.log("\n=== Summary ===");
  console.log(`  Issues scanned:        ${stats.scanned}`);
  console.log(`  Issue reminders:       ${stats.issueReminders}`);
  console.log(`  PR reminders:          ${stats.prReminders}`);
  console.log(`  Unassigned:            ${stats.unassigned}`);
  console.log(`  PRs closed:            ${stats.closed}`);
  console.log(`  Skipped (skip label):  ${stats.skipLabel}`);
  console.log(`  Skipped (no review):   ${stats.skipNoReview}`);
  console.log(`  Skipped (no assign ev):${stats.skipNoAssignEvent}`);
  console.log(`  Errors:                ${stats.errors}`);
  console.log(`  Dry run:               ${cfg.dryRun}`);

  // A per-issue error (e.g. a permission/API failure) silently disables actions for that
  // issue. Process the rest, then fail the run so the failure is visible instead of silent.
  if (stats.errors > 0) {
    throw new Error(`bot-contributor-lifecycle: ${stats.errors} issue(s) failed — see logs above.`);
  }
};
