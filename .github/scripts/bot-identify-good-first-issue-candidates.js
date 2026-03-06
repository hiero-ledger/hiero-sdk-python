// Ask CodeRabbit to identify GFI candidates and create tracking issues.

module.exports = async ({ github, context, core }) => {
  const owner = context.repo.owner;
  const repo = context.repo.repo;

  const TARGET_LABEL = 'Good First Issue Candidate';
  const TARGET_LABEL_DESCRIPTION = 'AI-identified issue that may be suitable for new contributors. Requires maintainer review.';
  const TARGET_LABEL_COLOR = 'C2E0C6';
  const CREATED_ISSUE_MARKER = '<!-- gfi-candidate-generated-issue -->';
  const COMMENT_MARKER = '<!-- gfi-candidate-coderabbit-review-request -->';
  const CODERABBIT_COMMENT = `${COMMENT_MARKER}\n@coderabbitai review\n\nPlease evaluate whether this issue is suitable as a Good First Issue Candidate for first-time contributors.\n\nRespond with a short verdict section using this exact format:\n- GFI_CANDIDATE: YES or NO\n- CONFIDENCE: LOW, MEDIUM, or HIGH\n- RATIONALE: one short paragraph\n\nFocus on scope size, clarity, dependencies, risk, and hidden complexity.`;

  const maxFromEnv = Number.parseInt(process.env.MAX_ISSUES_TO_LABEL || '5', 10);
  const MAX_LABELS_PER_RUN = Math.max(1, Math.min(50, Number.isFinite(maxFromEnv) ? maxFromEnv : 5));
  const requestCodeRabbit = String(process.env.REQUEST_CODERABBIT || 'true').toLowerCase() === 'true';

  // Labels that should always block candidate issue creation.
  const blockedLabelSet = new Set(['blocked', 'epic', 'architecture', 'security']);

  // Labels that indicate the source issue is already covered by good-first triage.
  const alreadyHandledLabelSet = new Set(['good first issue', 'good first issue candidate']);


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

  function evaluateIssue(issue) {
    const labels = normalizeLabels(issue.labels);

    // Hard safety gates only. Candidate suitability is decided by CodeRabbit.
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
    return {
      eligible: true,
      reason: 'Eligible for CodeRabbit assessment',
    };
  }

  function isCodeRabbitAuthor(comment) {
    const login = comment?.user?.login || '';
    const type = comment?.user?.type || '';
    return /coderabbit/i.test(login) || (/bot/i.test(type) && /coderabbit/i.test(comment?.body || ''));
  }

  function extractCodeRabbitVerdict(comments) {
    const reversed = [...comments].reverse();
    for (const comment of reversed) {
      if (!isCodeRabbitAuthor(comment)) {
        continue;
      }

      const body = String(comment.body || '');
      const normalized = body.toLowerCase();

      // Prefer explicit machine-readable verdict if present.
      const explicit = body.match(/GFI_CANDIDATE\s*:\s*(YES|NO)/i);
      if (explicit) {
        return {
          hasVerdict: true,
          isPositive: explicit[1].toUpperCase() === 'YES',
          source: 'explicit',
          commentId: comment.id,
        };
      }

      // Fallback to simple phrase detection from human-readable response.
      const positivePhrases = [
        'beginner-friendly',
        'good first issue candidate',
        'suitable for first-time contributors',
        'appropriate for new contributors',
      ];
      const negativePhrases = [
        'not beginner-friendly',
        'not suitable for first-time contributors',
        'too complex',
        'high complexity',
      ];

      const hasPositive = positivePhrases.some((p) => normalized.includes(p));
      const hasNegative = negativePhrases.some((p) => normalized.includes(p));

      if (hasPositive || hasNegative) {
        return {
          hasVerdict: true,
          isPositive: hasPositive && !hasNegative,
          source: 'heuristic',
          commentId: comment.id,
        };
      }
    }

    return { hasVerdict: false, isPositive: false };
  }

  async function listIssueComments(issueNumber) {
    return github.paginate(github.rest.issues.listComments, {
      owner,
      repo,
      issue_number: issueNumber,
      per_page: 100,
    });
  }

  async function hasExistingCodeRabbitRequest(issueNumber) {
    const comments = await listIssueComments(issueNumber);

    return comments.some((comment) => {
      const body = comment.body || '';
      return body.includes(COMMENT_MARKER) || body.includes('@coderabbitai review');
    });
  }

  async function getCodeRabbitDecision(issueNumber) {
    const comments = await listIssueComments(issueNumber);
    const verdict = extractCodeRabbitVerdict(comments);
    if (!verdict.hasVerdict) {
      return { approved: false, reason: 'No CodeRabbit verdict found yet' };
    }

    if (!verdict.isPositive) {
      return { approved: false, reason: 'CodeRabbit verdict is not positive for GFI candidate' };
    }

    return { approved: true, reason: `Positive CodeRabbit verdict (${verdict.source})`, verdict };
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

  function buildGeneratedIssueTitle(sourceIssue) {
    return `[GFI Candidate] #${sourceIssue.number} ${sourceIssue.title}`;
  }

  function buildGeneratedIssueBody(sourceIssue, decisionReason) {
    return [
      CREATED_ISSUE_MARKER,
      '',
      `Source Issue: #${sourceIssue.number}`,
      `Source URL: ${sourceIssue.html_url}`,
      '',
      'CodeRabbit identified this issue as potentially suitable for first-time contributors.',
      `Decision: ${decisionReason}`,
      '',
      'Maintainer checklist:',
      '- [ ] Confirm scope is small and localized',
      '- [ ] Confirm acceptance criteria are clear',
      '- [ ] Confirm no hidden blockers/dependencies',
      '- [ ] If approved, keep this issue and update labels as needed',
      '',
      `Reference marker: source-issue-${sourceIssue.number}`,
    ].join('\n');
  }

  async function hasGeneratedIssueForSource(sourceIssueNumber) {
    const query = `repo:${owner}/${repo} is:issue is:open in:body source-issue-${sourceIssueNumber}`;
    const { data } = await github.rest.search.issuesAndPullRequests({ q: query, per_page: 1 });
    return (data?.items?.length || 0) > 0;
  }

  async function createCandidateIssue(sourceIssue, decisionReason) {
    const alreadyExists = await hasGeneratedIssueForSource(sourceIssue.number);
    if (alreadyExists) {
      core.info(`Generated candidate issue already exists for source #${sourceIssue.number}; skipping creation.`);
      return false;
    }

    const { data: created } = await github.rest.issues.create({
      owner,
      repo,
      title: buildGeneratedIssueTitle(sourceIssue),
      body: buildGeneratedIssueBody(sourceIssue, decisionReason),
      labels: [TARGET_LABEL],
    });

    core.info(`Created candidate issue #${created.number} from source #${sourceIssue.number}`);
    return true;
  }

  async function getOpenIssuesToEvaluate() {
    // Repository-wide scan: evaluate all open issues on every trigger.
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
  let createdCount = 0;
  let evaluatedCount = 0;
  let skippedCount = 0;

  for (const issue of issues) {
    if (createdCount >= MAX_LABELS_PER_RUN) {
      core.warning(`Reached max candidate-issue cap (${MAX_LABELS_PER_RUN}) for this run. Stopping early.`);
      break;
    }

    evaluatedCount += 1;

    try {
      const result = evaluateIssue(issue);
      if (!result.eligible) {
        skippedCount += 1;
        core.info(`Skipped #${issue.number}: ${result.reason}`);
        continue;
      }

      // 1) Ensure CodeRabbit has been asked for an assessment.
      await maybeRequestCodeRabbit(issue.number);

      // 2) Create candidate issue only when CodeRabbit feedback is positive.
      const decision = await getCodeRabbitDecision(issue.number);
      if (!decision.approved) {
        skippedCount += 1;
        core.info(`Skipped creating candidate issue for #${issue.number}: ${decision.reason}`);
        continue;
      }

      const created = await createCandidateIssue(issue, decision.reason);
      if (created) {
        createdCount += 1;
      }
    } catch (error) {
      // Continue scanning even if one issue fails.
      const message = error && error.message ? error.message : String(error);
      core.warning(`Failed processing #${issue.number}: ${message}`);
    }
  }

  await core.summary
    .addHeading('Good First Issue Candidate Repo Scan Summary')
    .addTable([
      [{ data: 'Metric', header: true }, { data: 'Value', header: true }],
      ['Evaluated issues', String(evaluatedCount)],
      ['Candidate issues created', String(createdCount)],
      ['Skipped', String(skippedCount)],
      ['Max candidate issues per run', String(MAX_LABELS_PER_RUN)],
      ['CodeRabbit requests enabled', String(requestCodeRabbit)],
    ])
    .write();
};
