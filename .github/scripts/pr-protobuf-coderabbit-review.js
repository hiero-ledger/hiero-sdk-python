// Triggers a CodeRabbit full review with generated protobuf diff context for PRs.

const fs = require("fs");

const MARKER_PREFIX = "<!-- CodeRabbit Protobuf Review Trigger:";
const MAX_COMMENTS_TO_SCAN = 500;
const MAX_FILES_TO_LIST = 80;
const MAX_DIFF_CHARS = 12000;

function readTextFileOrEmpty(filePath) {
  if (!filePath || !fs.existsSync(filePath)) {
    return "";
  }

  return fs.readFileSync(filePath, "utf8");
}

function parseUniqueLines(text) {
  const seen = new Set();
  const lines = [];

  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || seen.has(line)) {
      continue;
    }
    seen.add(line);
    lines.push(line);
  }

  return lines;
}

function truncateDiff(diffText, maxChars = MAX_DIFF_CHARS) {
  if (diffText.length <= maxChars) {
    return {
      truncated: false,
      text: diffText,
    };
  }

  const slice = diffText.slice(0, maxChars);
  const lineBreakIndex = slice.lastIndexOf("\n");
  const safeSlice = lineBreakIndex > 0 ? slice.slice(0, lineBreakIndex) : slice;

  return {
    truncated: true,
    text: `${safeSlice}\n... (diff truncated in CI comment)`,
  };
}

async function hasExistingTriggerComment(github, owner, repo, issueNumber, marker) {
  try {
    const iterator = github.paginate.iterator(github.rest.issues.listComments, {
      owner,
      repo,
      issue_number: issueNumber,
      per_page: 100,
    });

    let scanned = 0;
    for await (const { data: page } of iterator) {
      for (const comment of page) {
        scanned += 1;
        if (typeof comment?.body === "string" && comment.body.includes(marker)) {
          return true;
        }
        if (scanned >= MAX_COMMENTS_TO_SCAN) {
          return false;
        }
      }
    }
  } catch (error) {
    console.log("Failed while checking existing protobuf trigger comments:", {
      message: error?.message,
      status: error?.status,
      owner,
      repo,
      issueNumber,
    });
    return false;
  }

  return false;
}

function buildCommentBody({
  marker,
  baseSha,
  headSha,
  changedFiles,
  diffSnippet,
  truncated,
  scopeMode,
  scopeReason,
}) {
  const fileLines = changedFiles
    .slice(0, MAX_FILES_TO_LIST)
    .map((filePath) => `- \`${filePath}\``);

  const hiddenCount = Math.max(0, changedFiles.length - MAX_FILES_TO_LIST);

  const fileList = fileLines.length > 0
    ? fileLines.join("\n")
    : "- (unable to compute changed generated files)";

  const hiddenLine = hiddenCount > 0 ? `\n- ...and ${hiddenCount} more files` : "";

  const truncatedSuffix = truncated ? " (truncated)" : "";

  return `${marker}
@coderabbitai full review

Generated protobuf build diff detected for this pull request.

- Base commit: \`${baseSha}\`
- Head commit: \`${headSha}\`
- Generated protobuf files changed: ${changedFiles.length}
- Scope mode: \`${scopeMode}\`
${scopeReason ? `- Scope detail: ${scopeReason}\n` : ""}

Please review this PR with focus on whether code changes remain aligned with these generated protobuf artifacts.

Changed generated protobuf files:
${fileList}${hiddenLine}

Generated protobuf diff excerpt${truncatedSuffix}:
\`\`\`diff
${diffSnippet}
\`\`\`
`;
}

async function createTriggerComment(github, owner, repo, issueNumber, body) {
  await github.rest.issues.createComment({
    owner,
    repo,
    issue_number: issueNumber,
    body,
  });
}

async function main({ github, context }) {
  const { owner, repo } = context.repo;
  const prNumber = context.payload?.pull_request?.number;

  if (!prNumber) {
    console.log("No pull request found in payload. Skipping.");
    return;
  }

  const baseSha = process.env.BASE_SHA || "";
  const headSha = process.env.HEAD_SHA || "";
  const diffPath = process.env.PROTOBUF_DIFF_PATH || "";
  const filesPath = process.env.PROTOBUF_FILES_PATH || "";
  const scopeMode = process.env.PROTOBUF_SCOPE_MODE || "full";
  const scopeReason = process.env.PROTOBUF_SCOPE_REASON || "";
  const isDryRun = (process.env.DRY_RUN || "false").toLowerCase() === "true";

  if (!baseSha || !headSha || !diffPath || !filesPath) {
    console.log("Missing required environment values. Skipping protobuf review trigger.", {
      hasBaseSha: Boolean(baseSha),
      hasHeadSha: Boolean(headSha),
      hasDiffPath: Boolean(diffPath),
      hasFilesPath: Boolean(filesPath),
    });
    return;
  }

  const fullDiff = readTextFileOrEmpty(diffPath);
  if (!fullDiff.trim()) {
    console.log("No generated protobuf diff found. Skipping CodeRabbit trigger.");
    return;
  }

  const changedFiles = parseUniqueLines(readTextFileOrEmpty(filesPath));
  const { text: diffSnippet, truncated } = truncateDiff(fullDiff, MAX_DIFF_CHARS);
  const marker = `${MARKER_PREFIX} ${headSha} -->`;

  if (await hasExistingTriggerComment(github, owner, repo, prNumber, marker)) {
    console.log(`CodeRabbit protobuf trigger already posted for PR #${prNumber} and head ${headSha}.`);
    return;
  }

  const body = buildCommentBody({
    marker,
    baseSha,
    headSha,
    changedFiles,
    diffSnippet,
    truncated,
    scopeMode,
    scopeReason,
  });

  if (isDryRun) {
    console.log(`[DRY RUN] Would create protobuf-triggered CodeRabbit comment for PR #${prNumber}.`);
    return;
  }

  try {
    await createTriggerComment(github, owner, repo, prNumber, body);
    console.log(`Posted protobuf-triggered CodeRabbit review comment on PR #${prNumber}.`);
  } catch (error) {
    if (error?.status === 403 || error?.status === 404) {
      console.log("Insufficient permissions to create PR comment in this context. Skipping.", {
        status: error?.status,
        owner,
        repo,
        prNumber,
      });
      return;
    }
    throw error;
  }
}

module.exports = main;
module.exports.hasExistingTriggerComment = hasExistingTriggerComment;
