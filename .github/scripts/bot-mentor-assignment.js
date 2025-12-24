const fs = require('fs');
const path = require('path');

const COMMENT_MARKER = process.env.COMMENT_MARKER || '<!-- Mentor Assignment Bot -->';
const MENTOR_TEAM_ALIAS = process.env.MENTOR_TEAM_ALIAS || '@hiero-ledger/hiero-sdk-python-triage';
const SUPPORT_TEAM_ALIAS = process.env.SUPPORT_TEAM_ALIAS || '@hiero-ledger/hiero-sdk-python-good-first-issue-support';
const DEFAULT_ROSTER_FILE = '.github/mentor_roster.json';

function loadMentorRoster() {
  const rosterPath = path.resolve(
    process.cwd(),
    process.env.MENTOR_ROSTER_PATH || DEFAULT_ROSTER_FILE,
  );

  let fileContents;
  try {
    fileContents = fs.readFileSync(rosterPath, 'utf8');
  } catch (error) {
    throw new Error(`Failed to read mentor roster at ${rosterPath}: ${error.message}`);
  }

  try {
    const parsed = JSON.parse(fileContents);
    const rawOrder = Array.isArray(parsed?.order) ? parsed.order : [];
    const roster = rawOrder
      .map((entry) => (typeof entry === 'string' ? entry.trim() : ''))
      .filter(Boolean);

    if (!roster.length) {
      throw new Error('Mentor roster is empty after filtering.');
    }

    return roster;
  } catch (error) {
    throw new Error(`Failed to parse mentor roster JSON: ${error.message}`);
  }
}

function selectMentor(roster, mentee) {
  if (!Array.isArray(roster) || roster.length === 0) {
    throw new Error('Mentor roster must contain at least one entry.');
  }

  const MILLISECONDS_PER_DAY = 24 * 60 * 60 * 1000;
  const dayNumber = Math.floor(Date.now() / MILLISECONDS_PER_DAY); // UTC day index
  const baseIndex = dayNumber % roster.length;
  const normalizedMentee = typeof mentee === 'string' ? mentee.toLowerCase() : null;

  for (let offset = 0; offset < roster.length; offset += 1) {
    const candidate = roster[(baseIndex + offset) % roster.length];

    if (!normalizedMentee || candidate.toLowerCase() !== normalizedMentee) {
      return candidate;
    }
  }

  return null;
}

function hasGoodFirstIssueLabel(issue) {
  return (issue.labels || []).some((label) => {
    const name = typeof label === 'string' ? label : label?.name;
    return typeof name === 'string' && name.toLowerCase() === 'good first issue';
  });
}

async function hasActiveMentorAssignment(github, owner, repo, mentee, currentIssueNumber) {
  try {
    const assignedIssues = await github.paginate(
      github.rest.issues.listForRepo,
      {
        owner,
        repo,
        assignee: mentee,
        state: 'open',
        per_page: 100,
      },
      (response) =>
        (response.data || []).filter((issue) => issue?.number && issue.number !== currentIssueNumber),
    );

    for (const assignedIssue of assignedIssues) {
      const comments = await github.paginate(github.rest.issues.listComments, {
        owner,
        repo,
        issue_number: assignedIssue.number,
        per_page: 100,
      });

      if (comments.some((comment) => comment.body?.includes(COMMENT_MARKER))) {
        return true;
      }
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.log(`Unable to detect existing mentor assignments for ${mentee}: ${message}`);
  }

  return false;
}

async function isNewContributor(github, owner, repo, login) {
  const query = `repo:${owner}/${repo} type:pr state:closed is:merged author:${login}`;

  try {
    const response = await github.rest.search.issuesAndPullRequests({
      q: query,
      per_page: 1,
    });
    return (response.data.total_count || 0) === 0;
  } catch (error) {
    console.log(`Unable to determine merged PRs for ${login}:`, error.message || error);
    // Return false (skip assignment) on API errors to avoid workflow failure
    return false;
  }
}

function buildComment({ mentee, mentor, owner, repo }) {
  const repoUrl = `https://github.com/${owner}/${repo}`;

  return `${COMMENT_MARKER}
👋 Hi @${mentee}, welcome to the Hiero Python SDK community!

You've been assigned this Good First Issue, and today’s on-call mentor from ${MENTOR_TEAM_ALIAS} is @${mentor}. They're here to help you land a great first contribution.

**How to get started**
- Review the issue description and any linked docs
- Share updates early and ask @${mentor} anything right here
- Keep the feedback loop short so we can support you quickly

Need more backup? ${SUPPORT_TEAM_ALIAS} is also on standby to cheer you on.

**Mentor:** @${mentor}
**Mentee:** @${mentee}

If you're enjoying the SDK, consider ⭐️ [starring the repository](${repoUrl}) so it's easy to find later.

Happy building!
— Python SDK Team`;
}

module.exports = async ({ github, context }) => {
  try {
    const issue = context.payload.issue;
    const assignee = context.payload.assignee;

    if (!issue?.number || !assignee?.login) {
      return console.log('No issue or assignee found in payload. Skipping.');
    }

    if (assignee.type === 'Bot') {
      return console.log(`Assignee ${assignee.login} is a bot. Skipping.`);
    }

    if (!hasGoodFirstIssueLabel(issue)) {
      return console.log(`Issue #${issue.number} is not labeled as Good First Issue. Skipping.`);
    }

    const { owner, repo } = context.repo;
    const mentee = assignee.login;

    // Ensure we haven't already posted a mentor assignment comment
    const existingComments = await github.paginate(github.rest.issues.listComments, {
      owner,
      repo,
      issue_number: issue.number,
      per_page: 100,
    });

    if (existingComments.some((comment) => comment.body?.includes(COMMENT_MARKER))) {
      return console.log(`Mentor assignment comment already exists on issue #${issue.number}. Skipping.`);
    }

    const isNewStarter = await isNewContributor(github, owner, repo, mentee);
    if (!isNewStarter) {
      return console.log(`${mentee} already has merged contributions. Skipping mentor assignment.`);
    }

    if (await hasActiveMentorAssignment(github, owner, repo, mentee, issue.number)) {
      return console.log(`${mentee} already has an active mentor assignment comment on another issue. Skipping.`);
    }

    const roster = loadMentorRoster();
    const mentor = selectMentor(roster, mentee);

    if (!mentor) {
      return console.log(`No eligible mentor (excluding mentee ${mentee}) found. Skipping mentor assignment.`);
    }

    console.log(`Assigning mentor @${mentor} to mentee @${mentee} for issue #${issue.number}.`);

    const comment = buildComment({ mentee, mentor, owner, repo });

    try {
      await github.rest.issues.createComment({
        owner,
        repo,
        issue_number: issue.number,
        body: comment,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);

      const freshComments = await github.paginate(github.rest.issues.listComments, {
        owner,
        repo,
        issue_number: issue.number,
        per_page: 100,
      });

      if (freshComments.some((existing) => existing.body?.includes(COMMENT_MARKER))) {
        return console.log(`Mentor assignment comment already exists on issue #${issue.number} after concurrent run. Skipping. (${message})`);
      }

      throw error;
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.log(`❌ Mentor assignment failed: ${message}`);
    throw error;
  }
};
