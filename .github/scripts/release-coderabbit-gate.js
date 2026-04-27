/**
 * Posts a single "@coderabbit review" comment on release PRs, embedding the
 * release review prompt. Designed to run with:
 * - permissions: contents: read, pull-requests: write
 *
 * Safety:
 * - Only runs for maintainer-authored PRs (MEMBER/OWNER)
 * - Dedupe via hidden marker comment
 */

const fs = require("fs");
const path = require("path");

const MARKER = "<!-- coderabbit-release-gate: v1 -->";


function loadPrompt() {
  const promptPath = path.join(
    process.env.GITHUB_WORKSPACE || ".",
    ".github/coderabbit/release-pr-prompt.md"
  );
  try {
    const content = fs.readFileSync(promptPath, "utf8").trim();
    if (!content) {
      throw new Error("Release prompt file is empty");
    }
    return content;
  } catch (error) {
    throw new Error(`Failed to load release prompt from ${promptPath}: ${error.message}`);
  }
}


async function commentAlreadyExists({ github, owner, repo, issue_number }) {
  try {
      const data = await github.paginate(github.rest.issues.listComments, {
      owner,
      repo,
      issue_number,
      per_page: 100,
      });
      data.forEach(c => {
        if (c.body && c.body.includes(MARKER)) {
            console.log(`FOUND MATCH in comment by ${c.user.login}: ${c.html_url}`);
        }
      });
        return data.some((c) => typeof c.body === "string" && c.body.includes(MARKER));
      }
  catch (error) {
      console.error(`Error checking for existing comments: ${error.message}`);
      return true; // Fail closed to avoid duplicates if we can't verify
      }
}


function buildBody({ prompt, headRef }) {
  return [
    "@coderabbit review",
    "",
    MARKER,
    "",
    "## 🚀 Release Gate: Cumulative Audit",
    "> **Notice to Reviewer**: This is a checkpoint PR for a new release. While the diff here primarily updates versioning and the Changelog, your audit must cover the **entire cumulative scope** of changes since the last version tag.",
    "",
    "### 🎯 Audit Objectives",
    "- Analyze all features merged into `main` since the previous release.",
    "- Identify breaking changes in the public API or protocol.",
    "- Verify architectural integrity across the Hiero SDK Python modules.",
    "",
    "<details>",
    "<summary><b>View Senior Audit Constraints</b></summary>",
    "",
    prompt,
    "",
    "</details>",
    "",
    "---",
    `*Auditing Branch: \`${headRef}\` against the project history.*`,
  ].join("\n");
}

function getSkipReason(pr) {
  if (!pr) {
    return "No pull_request payload; exiting.";
  }

  if (!["MEMBER", "OWNER"].includes(pr.author_association)) {
    return `author_association=${pr.author_association}; skipping.`;
  }

  const title = (pr.title || "").toLowerCase();
  const isReleaseTitle =
    title.startsWith("chore: release v") || title.startsWith("release v");

  if (!isReleaseTitle) {
    return "Not a release PR title; skipping.";
  }

  return null;
}

module.exports = async ({ github, context }) => {
  let issue_number = "unknown";
  let headRef = "?";
  let baseRef = "?";

  try {
    const owner = context.repo.owner;
    const repo = context.repo.repo;
    const pr = context.payload.pull_request;

    const skipReason = getSkipReason(pr);
    if (skipReason) {
      console.log(skipReason);
      return;
    }

    issue_number = pr.number;
    if (await commentAlreadyExists({ github, owner, repo, issue_number })) {
      console.log("Release gate comment already exists. Skipping.");
      return;
    }

    headRef = pr.head?.ref || "unknown";
    baseRef = pr.base?.ref || "unknown";

    const prompt = loadPrompt();
    const body = buildBody({ prompt, headRef });

    await github.rest.issues.createComment({
      owner,
      repo,
      issue_number,
      body,
    });

    console.log("Posted CodeRabbit release-gate comment.");
    console.log(`PR #${issue_number} (${headRef} → ${baseRef})`);
  } catch (error) {
    console.error(`Error in release PR coderabbit gate: ${error.message}`);
    console.log(`PR #${issue_number || 'unknown'} (${headRef || '?'} → ${baseRef || '?'})`);
  }
};
