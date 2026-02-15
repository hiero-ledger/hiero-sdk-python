function isBotLogin(login = "") {
  return /\[bot\]$/i.test(login) || /dependabot/i.test(login);
}

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

module.exports = async ({ github, context }) => {
  const isDryRun = /^true$/i.test(process.env.DRY_RUN || "");
  const prNumber = Number(process.env.PR_NUMBER) || context.payload.pull_request?.number;

  if (!prNumber) {
    throw new Error("PR number could not be determined.");
  }

  console.log(
    `[sync-issue-labels] Processing PR #${prNumber} in ${context.repo.owner}/${context.repo.repo} (dry_run=${isDryRun}).`
  );

  let prData;
  try {
    prData = await getPullRequestData({ github, context, prNumber });
  } catch (error) {
    throw new Error(`[sync-issue-labels] Failed to fetch PR #${prNumber}: ${error?.message || error}`);
  }
  const prAuthor = prData?.user?.login || "";

  if (isBotLogin(prAuthor)) {
    console.log(`[sync-issue-labels] Skipping bot-authored PR from ${prAuthor}.`);
    return;
  }

  const linkedIssueNumbers = extractLinkedIssueNumbers(prData?.body || "");
  if (!linkedIssueNumbers.length) {
    console.log("[sync-issue-labels] No linked issue references found in PR body.");
    return;
  }

  console.log(
    `[sync-issue-labels] Linked issues detected: ${linkedIssueNumbers.map((n) => `#${n}`).join(", ")}`
  );

  const labelsFromIssues = new Set();

  for (const issueNumber of linkedIssueNumbers) {
    try {
      const issueResponse = await github.rest.issues.get({
        owner: context.repo.owner,
        repo: context.repo.repo,
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

  if (!labelsFromIssues.size) {
    console.log("[sync-issue-labels] No labels found on linked issues. Nothing to sync.");
    return;
  }

  const prLabelNames = new Set(normalizeLabelNames(prData?.labels || []));
  const labelsToAdd = [...labelsFromIssues].filter((label) => !prLabelNames.has(label));

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
    await github.rest.issues.addLabels({
      owner: context.repo.owner,
      repo: context.repo.repo,
      issue_number: prNumber,
      labels: labelsToAdd,
    });

    console.log(`[sync-issue-labels] Added labels to PR #${prNumber}: ${labelsToAdd.join(", ")}`);
  } catch (error) {
    throw new Error(
      `[sync-issue-labels] Failed to add labels to PR #${prNumber}: ${error?.message || error}`
    );
  }
};
