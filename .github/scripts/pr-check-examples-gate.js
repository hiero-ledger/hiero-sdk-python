module.exports = async ({ github, context, core }) => {
  const isManualRun = context.eventName === "workflow_dispatch";
  const headSha = isManualRun ? context.sha : context.payload.check_suite.head_sha;
  core.setOutput("head_sha", headSha);

  if (isManualRun) {
    core.info("Manual dispatch: bypassing status gate.");
    core.setOutput("should_run", "true");
    return;
  }

  if (context.payload.check_suite.conclusion !== "success") {
    core.info(
      `Triggering check suite concluded as ${context.payload.check_suite.conclusion}; skipping examples.`
    );
    core.setOutput("should_run", "false");
    return;
  }

  if (
    !context.payload.check_suite.pull_requests ||
    context.payload.check_suite.pull_requests.length === 0
  ) {
    core.info("No pull request is associated with this check suite event; skipping examples.");
    core.setOutput("should_run", "false");
    return;
  }

  const owner = context.repo.owner;
  const repo = context.repo.repo;

  const checkRuns = await github.paginate(github.rest.checks.listForRef, {
    owner,
    repo,
    ref: headSha,
    per_page: 100,
  });

  const combinedStatus = await github.rest.repos.getCombinedStatusForRef({
    owner,
    repo,
    ref: headSha,
  });

  const requiredChecks = [
    { label: "Codacy Static Code Analysis", pattern: /^Codacy Static Code Analysis$/i },
    { label: "Code Coverage / coverage (pull_request)", pattern: /^coverage( \(pull_request\))?$/i },
    { label: "DCO", pattern: /^DCO$/i },
    {
      label: "PR Check – Broken Markdown Links / pr-check-broken-links (pull_request)",
      pattern: /^pr-check-broken-links( \(pull_request\))?$/i,
    },
    {
      label: "PR Changelog Check",
      pattern: /^(PR Changelog Check|changelog-check)( \(pull_request\))?$/i,
    },
    { label: "StepSecurity Harden-Runner", pattern: /^StepSecurity Harden-Runner$/i },
    { label: "StepSecurity Required Checks", pattern: /^StepSecurity Required Checks$/i },
  ];

  const requiredStatuses = ["codecov/patch", "codecov/project"];
  const missingOrFailed = [];

  for (const required of requiredChecks) {
    const matchingRuns = checkRuns.filter((run) => required.pattern.test(run.name));
    if (matchingRuns.length === 0) {
      missingOrFailed.push(`${required.label} (missing)`);
      continue;
    }

    const hasSuccess = matchingRuns.some((run) => run.conclusion === "success");
    if (!hasSuccess) {
      const conclusions = [
        ...new Set(matchingRuns.map((run) => run.conclusion || "pending")),
      ].join(", ");
      missingOrFailed.push(`${required.label} (${conclusions})`);
    }
  }

  for (const contextName of requiredStatuses) {
    const status = combinedStatus.data.statuses.find((item) => item.context === contextName);
    if (!status) {
      missingOrFailed.push(`${contextName} (missing)`);
      continue;
    }

    if (status.state !== "success") {
      missingOrFailed.push(`${contextName} (${status.state})`);
    }
  }

  if (missingOrFailed.length > 0) {
    core.info("Skipping examples: required checks are not all successful yet.");
    core.info(missingOrFailed.join("\n"));
    core.setOutput("should_run", "false");
    return;
  }

  const prNumber = context.payload.check_suite.pull_requests[0].number;
  const changedFiles = await github.paginate(github.rest.pulls.listFiles, {
    owner,
    repo,
    pull_number: prNumber,
    per_page: 100,
  });

  const runRelevantPatterns = [
    /^src\/.*\.(py|pyi)$/i,
    /^examples\/.*\.py$/i,
    /^tests\/.*\.py$/i,
    /^tck\/.*\.py$/i,
    /^scripts\/.*\.py$/i,
    /^generate_proto\.py$/i,
    /^pyproject\.toml$/i,
    /^uv\.lock$/i,
  ];

  const shouldRunForChanges = changedFiles.some((file) =>
    runRelevantPatterns.some((pattern) => pattern.test(file.filename))
  );

  if (!shouldRunForChanges) {
    const changedFileNames = changedFiles.map((file) => file.filename);
    core.info("Skipping examples: no runtime-relevant Python files changed in this PR.");
    core.info(`Changed files: ${changedFileNames.join(", ")}`);
    core.setOutput("should_run", "false");
    return;
  }

  core.info("All required checks are successful. Running examples.");
  core.setOutput("should_run", "true");
};
