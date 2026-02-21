// Checks if the given login belongs to a bot account (ends with [bot] or contains "dependabot").
function isBotLogin(login = "") {
  return /\[bot\]$/i.test(login) || /dependabot/i.test(login);
}

// Extracts issue numbers from PR body closing keywords (Fixes #123, Closes #456, Resolves #789, etc.).
function extractLinkedIssueNumbers(prBody = "") {
  const closingReferenceRegex =
    /\b(?:fix(?:es|ed)?|close(?:s|d)?|resolve(?:s|d)?)\s*:?\s*((?:#\d+)(?:\s*(?:,|and)\s*#\d+)*)/gi;
  const numbers = new Set();
  let referenceMatch;

  while ((referenceMatch = closingReferenceRegex.exec(prBody)) !== null) {
    const referencesText = referenceMatch[1] || "";
    const issueMatches = referencesText.matchAll(/#(\d+)/g);

    for (const issueMatch of issueMatches) {
      numbers.add(Number(issueMatch[1]));
    }
  }

  return [...numbers];
}

// Normalizes label objects/strings to an array of trimmed label names.
function normalizeLabelNames(labels = []) {
  const names = [];
  for (const label of labels) {
    if (typeof label === "string" && label.trim()) {
      names.push(label.trim());
      continue;
    }

    if (label && typeof label.name === "string" && label.name.trim()) {
      names.push(label.name.trim());
    }
  }
  return names;
}

// Fetches PR data from the payload or GitHub API if not present in payload.
async function getPullRequestData({ github, context, prNumber }) {
  if (context.payload.pull_request) {
    return context.payload.pull_request;
  }

  const response = await github.rest.pulls.get({
    owner: context.repo.owner,
    repo: context.repo.repo,
    pull_number: prNumber,
  });

  return response.data;
}

// Resolves PR number from environment or context, and determines if dry-run mode is enabled.
function resolveExecutionContext(context) {
  const isDryRun = /^true$/i.test(process.env.DRY_RUN || "");
  const prNumber = Number(process.env.PR_NUMBER) || context.payload.pull_request?.number;
  return { prNumber, isDryRun, owner: context.repo.owner, repo: context.repo.repo };
}

// Determines if the PR should be skipped (e.g., bot-authored PRs, no linked issues).
function shouldSkipPR(prData, linkedIssueNumbers) {
  const prAuthor = prData?.user?.login || "";

  if (isBotLogin(prAuthor)) {
    return { skip: true, reason: `Skipping bot-authored PR from ${prAuthor}.` };
  }

  if (!linkedIssueNumbers.length) {
    return { skip: true, reason: "No linked issue references found in PR body." };
  }

  return { skip: false };
}

// Collects labels from all linked issues, handling 404s and PR references.
async function collectLabelsFromLinkedIssues({ github, owner, repo, linkedIssueNumbers }) {
  const labelsFromIssues = new Set();

  for (const issueNumber of linkedIssueNumbers) {
    try {
      const issueResponse = await github.rest.issues.get({
        owner,
        repo,
        issue_number: issueNumber,
      });

      if (issueResponse?.data?.pull_request) {
        console.log(`[sync-issue-labels] Skipping #${issueNumber}: reference points to a pull request.`);
        continue;
      }

      const issueLabelNames = normalizeLabelNames(issueResponse?.data?.labels || []);
      console.log(
        `[sync-issue-labels] Issue #${issueNumber} labels: ${
          issueLabelNames.length ? issueLabelNames.join(", ") : "(none)"
        }`
      );

      for (const label of issueLabelNames) {
        labelsFromIssues.add(label);
      }
    } catch (error) {
      if (error?.status === 404) {
        console.log(`[sync-issue-labels] Linked issue #${issueNumber} not found. Skipping.`);
        continue;
      }

      throw error;
    }
  }

  return labelsFromIssues;
}

// Computes which labels should be added to the PR (missing from PR but present in issues).
function computeLabelsToAdd(prData, labelsFromIssues) {
  const prLabelNames = new Set(normalizeLabelNames(prData?.labels || []));
  return [...labelsFromIssues].filter((label) => !prLabelNames.has(label));
}

// Adds labels to the pull request via GitHub API.
async function addLabelsToPullRequest({ github, owner, repo, prNumber, labelsToAdd }) {
  await github.rest.issues.addLabels({
    owner,
    repo,
    issue_number: prNumber,
    labels: labelsToAdd,
  });

  console.log(`[sync-issue-labels] Added labels to PR #${prNumber}: ${labelsToAdd.join(", ")}`);
}

// Main entry point: syncs labels from linked issues to the PR.
module.exports = async ({ github, context }) => {
  const { prNumber, isDryRun, owner, repo } = resolveExecutionContext(context);

  if (!prNumber) {
    throw new Error("PR number could not be determined.");
  }

  console.log(
    `[sync-issue-labels] Processing PR #${prNumber} in ${owner}/${repo} (dry_run=${isDryRun}).`
  );

  let prData;
  try {
    prData = await getPullRequestData({ github, context, prNumber });
  } catch (error) {
    throw new Error(`[sync-issue-labels] Failed to fetch PR #${prNumber}: ${error?.message || error}`);
  }

  const linkedIssueNumbers = extractLinkedIssueNumbers(prData?.body || "");
  const skipResult = shouldSkipPR(prData, linkedIssueNumbers);

  if (skipResult.skip) {
    console.log(`[sync-issue-labels] ${skipResult.reason}`);
    return;
  }

  console.log(
    `[sync-issue-labels] Linked issues detected: ${linkedIssueNumbers.map((n) => `#${n}`).join(", ")}`
  );

  const labelsFromIssues = await collectLabelsFromLinkedIssues({
    github,
    owner,
    repo,
    linkedIssueNumbers,
  });

  if (!labelsFromIssues.size) {
    console.log("[sync-issue-labels] No labels found on linked issues. Nothing to sync.");
    return;
  }

  const labelsToAdd = computeLabelsToAdd(prData, labelsFromIssues);
  const prLabelNames = new Set(normalizeLabelNames(prData?.labels || []));

  console.log(
    `[sync-issue-labels] Existing PR labels: ${
      prLabelNames.size ? [...prLabelNames].join(", ") : "(none)"
    }`
  );
  console.log(
    `[sync-issue-labels] Labels to add: ${labelsToAdd.length ? labelsToAdd.join(", ") : "(none)"}`
  );

  if (!labelsToAdd.length) {
    console.log("[sync-issue-labels] PR already contains all labels from linked issues.");
    return;
  }

  if (isDryRun) {
    console.log(`[sync-issue-labels] DRY_RUN enabled; would add labels: ${labelsToAdd.join(", ")}`);
    return;
  }

  try {
    await addLabelsToPullRequest({ github, owner, repo, prNumber, labelsToAdd });
  } catch (error) {
    throw new Error(
      `[sync-issue-labels] Failed to add labels to PR #${prNumber}: ${error?.message || error}`
    );
  }
};
