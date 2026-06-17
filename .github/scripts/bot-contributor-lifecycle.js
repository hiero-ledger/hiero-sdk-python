/*
------------------------------------------------------------------------------
Contributor Lifecycle Bot

Replaces three former bots (one daily scan, one source of truth):
  - cron-reminder-issue-no-pr   (remind assignee, issue has no PR)
  - cron-reminder-pr-inactive   (remind PR author, no activity)
  - bot-inactivity-unassign     (unassign idle assignees / close stale reviewed PRs)

Runs on a schedule via actions/github-script. Scans every OPEN issue that has
assignees (not PRs). For each assignee it applies a staged escalation:

  Issue has NO linked open PR:
    age >= ISSUE_UNASSIGN_DAYS  -> comment + unassign
    age >= ISSUE_REMIND_DAYS    -> reminder (once, marker-guarded)
    else                        -> keep

  Issue HAS linked open PR(s) (per PR):
    'discussion' label          -> skip
    no human review             -> keep (never close an un-reviewed PR)
    reviewed, age >= PR_CLOSE_DAYS  -> comment + close PR + unassign issue
    reviewed, age >= PR_REMIND_DAYS -> reminder on PR (once, marker-guarded)
    else                        -> keep

"age" is measured from the most recent activity, which always includes a recent
`/working` comment from the assignee — so `/working` resets every timer. PR age
also includes the last commit and the last human (non-bot, non-author) review.

DRY_RUN=true logs intended actions and mutates nothing.

Config (env, all override-able for fork testing — set to 0 to fire immediately):
  ISSUE_REMIND_DAYS=7  ISSUE_UNASSIGN_DAYS=21  PR_REMIND_DAYS=10  PR_CLOSE_DAYS=60
------------------------------------------------------------------------------
*/

const DAY_MS = 24 * 60 * 60 * 1000;

// HTML markers — reused from the old bots so issues/PRs they already pinged are
// not re-pinged. Enforcement markers are for traceability (close/unassign are
// also state-idempotent).
const MARK_ISSUE_REMIND = "<!-- issue-reminder-bot -->";
const MARK_PR_REMIND = "<!-- pr-inactivity-bot-marker -->";
const MARK_UNASSIGN = "<!-- inactivity-unassign-bot -->";
const MARK_CLOSE = "<!-- inactivity-close-bot -->";

const WORKING_RE = /(^|\s)\/working(\s|$)/i;

const DISCORD_LINK =
  "[Discord](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/discord.md)";
const OFFICE_HOURS =
  "[Office Hours](https://zoom-lfx.platform.linuxfoundation.org/meetings/hiero?view=week)";

// ---- small pure helpers ----

function intEnv(name, def) {
  const raw = process.env[name];
  if (raw === undefined || raw === null || raw === "") return def;
  const v = parseInt(raw, 10);
  return Number.isFinite(v) && v >= 0 ? v : def;
}

function readConfig() {
  return {
    issueRemindDays: intEnv("ISSUE_REMIND_DAYS", 7),
    issueUnassignDays: intEnv("ISSUE_UNASSIGN_DAYS", 21),
    prRemindDays: intEnv("PR_REMIND_DAYS", 10),
    prCloseDays: intEnv("PR_CLOSE_DAYS", 60),
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

function hasMarker(comments, marker) {
  return comments.some((c) => typeof c.body === "string" && c.body.includes(marker));
}

// Latest `/working` comment from a specific user (Date or null).
function lastWorkingAt(comments, user) {
  let latest = null;
  for (const c of comments) {
    if (c?.user?.login !== user) continue;
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

// Open PRs in THIS repo linked to the issue — unified detector combining
// closedBy references (closing keywords) and cross-references (any mention).
function linkedOpenPRNumbers(graph, nameWithOwner) {
  const issue = graph?.repository?.issue;
  const set = new Set();
  for (const n of issue?.closedByPullRequestsReferences?.nodes || []) {
    if (n?.state === "OPEN" && n?.repository?.nameWithOwner === nameWithOwner && n.number) {
      set.add(n.number);
    }
  }
  for (const n of issue?.crossRefs?.nodes || []) {
    const s = n?.source;
    if (s?.state === "OPEN" && s?.repository?.nameWithOwner === nameWithOwner && s.number) {
      set.add(s.number);
    }
  }
  return [...set];
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
  const query = `
    query($owner:String!, $repo:String!, $number:Int!) {
      repository(owner:$owner, name:$repo) {
        issue(number:$number) {
          assignedEvents: timelineItems(itemTypes:[ASSIGNED_EVENT], last:100) {
            nodes { ... on AssignedEvent { createdAt assignee { ... on User { login } } } }
          }
          crossRefs: timelineItems(itemTypes:[CROSS_REFERENCED_EVENT], first:100) {
            nodes {
              ... on CrossReferencedEvent {
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
    if (!r.user || r.user.type === "Bot") continue;
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
    return new Date(commit?.committer?.date || commit?.author?.date || pr.created_at);
  } catch (err) {
    console.log(`  [WARN] Could not fetch head commit for PR #${pr.number}:`, err.message || err);
    return null;
  }
}

// ---- message builders ----

function issueReminderBody(assignee) {
  return `${MARK_ISSUE_REMIND}
Hi @${assignee} 👋

This issue has been assigned but no pull request has been created yet.
Are you still planning on working on it?
If you are, please create a draft PR linked to this issue or comment \`/working\` to let us know.
If you're no longer able to work on this issue, you can comment \`/unassign\` to release it.

From the Python SDK Team`;
}

function issueUnassignBody(assignee, ageDays) {
  return `${MARK_UNASSIGN}
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

function prCloseBody(assignee, ageDays) {
  return `${MARK_CLOSE}
Hi @${assignee}, this is CronInactivityBot 👋

This pull request has been reviewed but has had no new activity for **${ageDays} days**, so I'm closing it and unassigning you from the linked issue to keep the backlog healthy.

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

async function handleNoPR(github, owner, repo, issue, assignee, baseline, comments, nowMs, cfg, stats) {
  const ageDays = daysSince(baseline, nowMs);
  console.log(`    [INFO] No linked open PR; age ~${ageDays}d`);

  if (ageDays >= cfg.issueUnassignDays) {
    console.log(`    [RESULT] Stale assignment (>= ${cfg.issueUnassignDays}d, no PR) -> unassign`);
    await postComment(github, owner, repo, issue.number, issueUnassignBody(assignee, ageDays), cfg);
    await removeAssignee(github, owner, repo, issue.number, assignee, cfg);
    stats.unassigned++;
    return;
  }

  if (ageDays >= cfg.issueRemindDays) {
    if (hasMarker(comments, MARK_ISSUE_REMIND)) {
      console.log(`    [SKIP] Issue already has a reminder comment`);
      return;
    }
    console.log(`    [RESULT] Idle assignment (>= ${cfg.issueRemindDays}d, no PR) -> remind`);
    await postComment(github, owner, repo, issue.number, issueReminderBody(assignee), cfg);
    stats.issueReminders++;
    return;
  }

  console.log(`    [KEEP] Assignment fresh (< ${cfg.issueRemindDays}d)`);
}

async function handleLinkedPRs(github, owner, repo, issue, assignee, prNumbers, workingAt, nowMs, cfg, stats) {
  for (const prNum of prNumbers) {
    let pr;
    try {
      pr = (await github.rest.pulls.get({ owner, repo, pull_number: prNum })).data;
    } catch (err) {
      console.log(`    [SKIP] Could not fetch PR #${prNum}:`, err.message || err);
      continue;
    }
    if (pr.state !== "open") {
      console.log(`    [SKIP] PR #${prNum} is ${pr.state}`);
      continue;
    }
    if ((pr.labels || []).some((l) => (l.name || "").toLowerCase() === "discussion")) {
      console.log(`    [SKIP] PR #${prNum} has 'discussion' label`);
      continue;
    }

    const reviewDate = await lastHumanReviewDate(github, owner, repo, prNum, pr.user?.login);
    if (!reviewDate) {
      console.log(`    [KEEP] PR #${prNum} has no human review yet -> not eligible for reminder/close`);
      continue;
    }

    const commitDate = await lastCommitDate(github, pr);
    const activity = maxDate([reviewDate, commitDate, workingAt]);
    const ageDays = daysSince(activity, nowMs);
    console.log(`    [INFO] PR #${prNum} reviewed; last activity ~${ageDays}d ago`);

    if (ageDays >= cfg.prCloseDays) {
      console.log(`    [RESULT] PR #${prNum} stale (>= ${cfg.prCloseDays}d) -> close + unassign`);
      await postComment(github, owner, repo, prNum, prCloseBody(assignee, ageDays), cfg);
      await closePR(github, owner, repo, prNum, cfg);
      await removeAssignee(github, owner, repo, issue.number, assignee, cfg);
      stats.closed++;
      continue;
    }

    if (ageDays >= cfg.prRemindDays) {
      let prComments;
      try {
        prComments = await listIssueComments(github, owner, repo, prNum);
      } catch (err) {
        console.log(`    [SKIP] Could not list comments for PR #${prNum} (avoid duplicate):`, err.message || err);
        continue;
      }
      if (hasMarker(prComments, MARK_PR_REMIND)) {
        console.log(`    [SKIP] PR #${prNum} already has an inactivity reminder`);
        continue;
      }
      console.log(`    [RESULT] PR #${prNum} inactive (>= ${cfg.prRemindDays}d) -> remind`);
      await postComment(github, owner, repo, prNum, prReminderBody(pr.user?.login || assignee, ageDays), cfg);
      stats.prReminders++;
      continue;
    }

    console.log(`    [KEEP] PR #${prNum} active (< ${cfg.prRemindDays}d)`);
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
  console.log(`  Dry run: ${cfg.dryRun}`);
  console.log("------------------------------------------------------------");

  const stats = { issueReminders: 0, prReminders: 0, unassigned: 0, closed: 0, scanned: 0 };

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

    console.log(`\n== ISSUE #${issue.number} ==`);

    try {
      const comments = await listIssueComments(github, owner, repo, issue.number);
      const graph = await fetchIssueGraph(github, owner, repo, issue.number);
      const prNumbers = linkedOpenPRNumbers(graph, nameWithOwner);

      for (const assignee of issue.assignees.map((a) => a.login)) {
        console.log(`  -> assignee @${assignee}`);

        const assignedAt = assignmentDateFor(graph, assignee);
        if (!assignedAt) {
          console.log(`    [WARN] No assignment event found; skipping for safety`);
          continue;
        }

        const workingAt = lastWorkingAt(comments, assignee);

        if (prNumbers.length === 0) {
          // Issue stage: baseline is the latest of assignment or a /working signal.
          const baseline = maxDate([assignedAt, workingAt]);
          await handleNoPR(github, owner, repo, issue, assignee, baseline, comments, nowMs, cfg, stats);
        } else {
          console.log(`    [INFO] Linked open PRs: ${prNumbers.join(", ")}`);
          await handleLinkedPRs(github, owner, repo, issue, assignee, prNumbers, workingAt, nowMs, cfg, stats);
        }
      }
    } catch (err) {
      console.log(`  [ERROR] Issue #${issue.number} failed:`, err.message || err);
    }
  }

  console.log("\n=== Summary ===");
  console.log(`  Issues scanned:   ${stats.scanned}`);
  console.log(`  Issue reminders:  ${stats.issueReminders}`);
  console.log(`  PR reminders:     ${stats.prReminders}`);
  console.log(`  Unassigned:       ${stats.unassigned}`);
  console.log(`  PRs closed:       ${stats.closed}`);
  console.log(`  Dry run:          ${cfg.dryRun}`);
};
