// Identify beginner-friendly issues and label them as Good First Issue Candidate.

module.exports = async ({ github, context, core }) => {
  const owner = context.repo.owner;
  const repo = context.repo.repo;

  const TARGET_LABEL = 'Good First Issue Candidate';
  const TARGET_LABEL_DESCRIPTION = 'AI-identified issue that may be suitable for new contributors. Requires maintainer review.';
  const TARGET_LABEL_COLOR = 'C2E0C6';
  const COMMENT_MARKER = '<!-- gfi-candidate-coderabbit-review-request -->';
  const CODERABBIT_COMMENT = `${COMMENT_MARKER}\n@coderabbitai review\n\nPlease evaluate whether this issue appears beginner-friendly for a first-time contributor. Focus on scope, clarity, dependencies, and potential hidden complexity.`;

  const maxFromEnv = Number.parseInt(process.env.MAX_ISSUES_TO_LABEL || '5', 10);
  const MAX_LABELS_PER_RUN = Math.max(1, Math.min(50, Number.isFinite(maxFromEnv) ? maxFromEnv : 5));
  const requestCodeRabbit = String(process.env.REQUEST_CODERABBIT || 'true').toLowerCase() === 'true';

  // Labels that should always block candidate labeling.
  const blockedLabelSet = new Set(['blocked', 'epic', 'architecture', 'security']);

  // Labels that indicate the issue is already covered by good-first triage.
  const alreadyHandledLabelSet = new Set(['good first issue', 'good first issue candidate']);

  const beginnerKeywords = [
    'docs',
    'documentation',
    'typo',
    'readme',
    'test',
    'tests',
    'unit test',
    'integration test',
    'minor',
    'small',
    'simple',
    'cleanup',
    'refactor',
    'validation',
    'error message',
    'bug',
    'fix',
    'edge case',
  ];

  const nonBeginnerKeywords = [
    'architecture',
    'redesign',
    'security',
    'vulnerability',
    'performance',
    'latency',
    'throughput',
    'scalability',
    'protocol change',
    'consensus',
    'cryptography',
    'breaking change',
    'deep domain knowledge',
  ];

  const claritySignals = [
    /steps?\s+to\s+reproduce/i,
    /expected\s+behavior/i,
    /actual\s+behavior/i,
    /acceptance\s+criteria/i,
    /definition\s+of\s+done/i,
    /reproduc(e|ible)/i,
    /how\s+to\s+reproduce/i,
  ];

  async function ensureLabelExists() {
    try {
      await github.rest.issues.getLabel({ owner, repo, name: TARGET_LABEL });
    } catch (error) {
      if (error.status === 404) {
        await github.rest.issues.createLabel({
          owner,
          repo,
          name: TARGET_LABEL,
          color: TARGET_LABEL_COLOR,
          description: TARGET_LABEL_DESCRIPTION,
        });
        core.info(`Created missing label: ${TARGET_LABEL}`);
      } else {
        throw error;
      }
    }
  }

  function normalizeLabels(labels) {
    return new Set((labels || []).map((l) => (l.name || '').trim().toLowerCase()));
  }

  function includesAnyKeyword(text, keywords) {
    const lower = text.toLowerCase();
    return keywords.some((kw) => lower.includes(kw));
  }

  function hasClaritySignals(body) {
    if (!body || body.trim().length < 80) {
      return false;
    }
    return claritySignals.some((pattern) => pattern.test(body));
  }

  function evaluateIssue(issue) {
    const labels = normalizeLabels(issue.labels);
    const title = issue.title || '';
    const body = issue.body || '';
    const content = `${title}\n${body}`;

    // Hard stops first.
    if (issue.pull_request) {
      return { eligible: false, reason: 'Not an issue' };
    }
    if ((issue.assignees || []).length > 0) {
      return { eligible: false, reason: 'Issue already assigned' };
    }
    if ([...labels].some((name) => blockedLabelSet.has(name))) {
      return { eligible: false, reason: 'Issue is blocked by high-complexity label' };
    }
    if ([...labels].some((name) => alreadyHandledLabelSet.has(name))) {
      return { eligible: false, reason: 'Already has good-first related label' };
    }

    // Soft scoring heuristic.
    let score = 0;

    if (includesAnyKeyword(content, beginnerKeywords)) {
      score += 2;
    }

    if (hasClaritySignals(body)) {
      score += 2;
    }

    // Scope indicators in title/body.
    if (/\b(small|minor|localized|single file|low risk)\b/i.test(content)) {
      score += 1;
    }

    // Prefer unblocked, unassigned, and actionable issues.
    if (/\b(docs?|tests?|validation|error messages?|refactor|bug fix|cleanup)\b/i.test(content)) {
      score += 1;
    }

    if (includesAnyKeyword(content, nonBeginnerKeywords)) {
      score -= 3;
    }

    // Require at least one clarity or scoped-work signal.
    const hasScopeOrClarity =
      hasClaritySignals(body) || /\b(small|minor|docs?|tests?|validation|error messages?)\b/i.test(content);

    if (!hasScopeOrClarity) {
      return { eligible: false, reason: 'Insufficient clarity/scope signal', score };
    }

    return {
      eligible: score >= 2,
      reason: score >= 2 ? 'Heuristic score meets threshold' : 'Heuristic score below threshold',
      score,
    };
  }

  async function hasExistingCodeRabbitRequest(issueNumber) {
    const comments = await github.paginate(github.rest.issues.listComments, {
      owner,
      repo,
      issue_number: issueNumber,
      per_page: 100,
    });

    return comments.some((comment) => {
      const body = comment.body || '';
      return body.includes(COMMENT_MARKER) || body.includes('@coderabbitai review');
    });
  }

  async function maybeRequestCodeRabbit(issueNumber) {
    if (!requestCodeRabbit) {
      return;
    }

    const exists = await hasExistingCodeRabbitRequest(issueNumber);
    if (exists) {
      core.info(`CodeRabbit request already exists on #${issueNumber}; skipping comment.`);
      return;
    }

    await github.rest.issues.createComment({
      owner,
      repo,
      issue_number: issueNumber,
      body: CODERABBIT_COMMENT,
    });
    core.info(`Posted CodeRabbit request comment on #${issueNumber}`);
  }

  async function addCandidateLabel(issueNumber) {
    await github.rest.issues.addLabels({
      owner,
      repo,
      issue_number: issueNumber,
      labels: [TARGET_LABEL],
    });
    core.info(`Added '${TARGET_LABEL}' to #${issueNumber}`);
  }

  async function getOpenIssuesToEvaluate() {
    const eventName = process.env.EVENT_NAME;
    const eventAction = process.env.EVENT_ACTION;
    const issueNumberRaw = process.env.EVENT_ISSUE_NUMBER;

    // For issue lifecycle events, evaluate only the changed issue to reduce API load.
    if (eventName === 'issues' && issueNumberRaw) {
      const issueNumber = Number.parseInt(issueNumberRaw, 10);
      if (Number.isFinite(issueNumber)) {
        const { data: issue } = await github.rest.issues.get({
          owner,
          repo,
          issue_number: issueNumber,
        });
        if (issue.state === 'open') {
          core.info(`Evaluating single issue from event: #${issue.number} (${eventAction})`);
          return [issue];
        }
        return [];
      }
    }

    // For scheduled/manual runs, scan all open issues.
    const issues = await github.paginate(github.rest.issues.listForRepo, {
      owner,
      repo,
      state: 'open',
      per_page: 100,
      sort: 'updated',
      direction: 'desc',
    });

    const onlyIssues = issues.filter((i) => !i.pull_request);
    core.info(`Loaded ${onlyIssues.length} open issues for scanning.`);
    return onlyIssues;
  }

  await ensureLabelExists();

  const issues = await getOpenIssuesToEvaluate();
  let labeledCount = 0;
  let evaluatedCount = 0;
  let skippedCount = 0;

  for (const issue of issues) {
    if (labeledCount >= MAX_LABELS_PER_RUN) {
      core.warning(`Reached max label cap (${MAX_LABELS_PER_RUN}) for this run. Stopping early.`);
      break;
    }

    evaluatedCount += 1;

    try {
      const result = evaluateIssue(issue);
      if (!result.eligible) {
        skippedCount += 1;
        core.info(
          `Skipped #${issue.number}: ${result.reason}${typeof result.score === 'number' ? ` (score=${result.score})` : ''}`
        );
        continue;
      }

      await addCandidateLabel(issue.number);
      await maybeRequestCodeRabbit(issue.number);
      labeledCount += 1;
    } catch (error) {
      // Continue scanning even if one issue fails.
      const message = error && error.message ? error.message : String(error);
      core.warning(`Failed processing #${issue.number}: ${message}`);
    }
  }

  await core.summary
    .addHeading('Good First Issue Candidate Scan Summary')
    .addTable([
      [{ data: 'Metric', header: true }, { data: 'Value', header: true }],
      ['Evaluated issues', String(evaluatedCount)],
      ['Labeled as candidates', String(labeledCount)],
      ['Skipped', String(skippedCount)],
      ['Max labels per run', String(MAX_LABELS_PER_RUN)],
      ['CodeRabbit requests enabled', String(requestCodeRabbit)],
    ])
    .write();
};
