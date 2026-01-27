const fs = require('fs');
const path = require('path');

const COMMENT_MARKER = process.env.COMMENT_MARKER || '<!-- Mentor Assignment Bot -->';
const MENTOR_TEAM_ALIAS = process.env.MENTOR_TEAM_ALIAS || '@hiero-ledger/hiero-sdk-python-triage';
const SUPPORT_TEAM_ALIAS = process.env.SUPPORT_TEAM_ALIAS || '@hiero-ledger/hiero-sdk-good-first-issue-support';
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

function selectMentor(roster) {
  if (!Array.isArray(roster) || roster.length === 0) {
    throw new Error('Mentor roster must contain at least one entry.');
  }

  const MILLISECONDS_PER_DAY = 24 * 60 * 60 * 1000;
  const dayNumber = Math.floor(Date.now() / MILLISECONDS_PER_DAY); // UTC day index
  const index = dayNumber % roster.length;

  return roster[index];
}

function hasGoodFirstIssueLabel(issue) {
  return (issue.labels || []).some((label) => {
    const name = typeof label === 'string' ? label : label?.name;
    return typeof name === 'string' && name.toLowerCase() === 'good first issue';
  });
}

async function isNewContributor(github, owner, repo, login) {
  let targetOwner = owner;
  let targetRepo = repo;

  console.log(`Checking contributor status for ${login} in ${owner}/${repo}`);

  try {
    const repoData = await github.rest.repos.get({ owner, repo });
    console.log(`Repository fork status: ${repoData.data.fork}`);
    if (repoData.data.fork && repoData.data.parent) {
      targetOwner = repoData.data.parent.owner.login;
      targetRepo = repoData.data.parent.name;
      console.log(`Detected fork. Using parent repository: ${targetOwner}/${targetRepo}`);
    } else {
      console.log(`Not a fork or no parent found. Using current repository: ${targetOwner}/${targetRepo}`);
    }
  } catch (error) {
    console.log(`Unable to check if repository is a fork: ${error.message || error}`);
  }

  try {
    console.log(`Checking for merged PRs by ${login} in ${targetOwner}/${targetRepo}`);
    
    const iterator = github.paginate.iterator(github.rest.pulls.list, {
      owner: targetOwner,
      repo: targetRepo,
      state: 'closed',
      sort: 'updated',
      direction: 'desc',
      per_page: 100,
    });

    for await (const { data: pullRequests } of iterator) {
      const mergedPR = pullRequests.find(pr => pr.user?.login === login && pr.merged_at !== null);
      if (mergedPR) {
        console.log(`Found merged PR #${mergedPR.number} by ${login}. Not a new contributor.`);
        return false;
      }
    }
    
    console.log(`No merged PRs found for ${login}. Considered a new starter.`);
    return true;
  } catch (error) {
    console.log(`Unable to determine merged PRs for ${login}:`, error.message || error);
    // Return null (skip assignment) on API errors to avoid workflow failure while preserving accurate logging
    return null;
  }
}

function buildComment({ mentee, mentor, owner, repo }) {
    const repoUrl = owner && repo ? `https://github.com/${owner}/${repo}` : "https://github.com/hiero-ledger/hiero-sdk-python";

    return `${COMMENT_MARKER}👋 Hi @${mentee}, welcome to the Hiero Python SDK community!
You've been assigned this **Good First Issue**. Your on-call mentor today from ${MENTOR_TEAM_ALIAS} is **@${mentor}**, and the **Good First Issue Support Team** is **${SUPPORT_TEAM_ALIAS}**.
We’re here to help you get your first PR merged successfully 🚀

---
### Step 1: Read the task
- Open the issue description, carefully read the requirements and workflow
- Read any linked documentation
- Make sure you understand the expected outcome
If anything is unclear, ask your mentor **before** writing code.

---
### Step 2: Tell us your plan (in this thread)
Reply here with:
- What you think the task is
- What you plan to change to solve the issue requirement and no more
- Any questions you have
This means we can guide you early on, helping you to have a more stress free experience

---
### Step 3: Get the right kind of help
Finishing your first PR can be really hard. We are here to help you - please ask us!

🛠 **Good First Issue Support Team (${SUPPORT_TEAM_ALIAS})**
Use them for **workflow and GitHub issues**, such as:
- Failing CI checks
- Commit signing problems
- Merge conflicts
- Git/GitHub errors
They can also jump on a call if needed.

🐍 **Your Mentor (@${mentor})**
Use your mentor for **Python and code guidance**, such as:
- Which files to edit
- How to structure your solution
- Docstring and code style questions
- Making sure your PR meets the issue requirements

💬 **Discord (for fast help)**
Guide: [Join the Python SDK Discord](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/discord.md)
Use Discord when you need **immediate answers** from the community, like:
- What docs to read
- How to unblock yourself quickly
- Clarifying next steps in real time

---
**Mentor:** @${mentor}
**Mentee:** @${mentee}
If you're enjoying the SDK, consider ⭐️ [starring the repository](${repoUrl}) so it's easy to find later.
Happy building!
— Python SDK Team`;
}

module.exports = async ({ github, context, assignee: passedAssignee }) => {
  try {
    const issue = context.payload.issue;
    const assignee = passedAssignee || context.payload.assignee;

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

    if (isNewStarter === null) {
      return console.log(`Unable to confirm whether ${mentee} is a new contributor due to API error. Skipping mentor assignment.`);
    }

    if (!isNewStarter) {
      return console.log(`${mentee} already has merged contributions. Skipping mentor assignment.`);
    }

    const roster = loadMentorRoster();
    const mentor = selectMentor(roster);

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
