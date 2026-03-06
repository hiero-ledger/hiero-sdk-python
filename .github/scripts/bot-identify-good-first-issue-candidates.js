const crypto = require("node:crypto");

module.exports = async ({ github, context, core, rawOutput }) => {
  const owner = context.repo.owner;
  const repo = context.repo.repo;

  const TARGET_LABEL = "Good First Issue Candidate";
  const TARGET_LABEL_DESCRIPTION =
    "Automatically identified issue that may be suitable for new contributors. Requires maintainer review.";
  const TARGET_LABEL_COLOR = "C2E0C6";

  const MAX_ISSUES_PER_RUN = clampInt(process.env.MAX_ISSUES_PER_RUN, 5, 1, 20);

  // Heuristics: prefer localized, lower-risk, clearer findings.
  const POSITIVE_KEYWORDS = [
    "documentation",
    "docs",
    "readme",
    "error message",
    "validation",
    "missing test",
    "tests",
    "type hint",
    "typing",
    "null check",
    "logic error",
    "unused",
    "small refactor",
    "edge case",
    "clarity",
  ];

  const NEGATIVE_KEYWORDS = [
    "security vulnerability",
    "race condition",
    "memory leak",
    "sql injection",
    "authentication",
    "authorization",
    "crypto",
    "consensus",
    "architecture",
    "redesign",
    "performance bottleneck",
    "distributed",
    "breaking change",
    "cross-cutting",
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

  function clampInt(raw, fallback, min, max) {
    const parsed = Number.parseInt(String(raw ?? fallback), 10);
    if (!Number.isFinite(parsed)) return fallback;
    return Math.max(min, Math.min(max, parsed));
  }

  function normalizeText(text) {
    return String(text || "").toLowerCase().replace(/\s+/g, " ").trim();
  }

  function sha(input) {
    return crypto.createHash("sha1").update(input).digest("hex").slice(0, 14);
  }

  function candidateMarker(key) {
    return `<!-- gfi-candidate-key:${key} -->`;
  }

  async function getOpenIssues() {
    const issues = await github.paginate(github.rest.issues.listForRepo, {
      owner,
      repo,
      state: "open",
      per_page: 100,
      sort: "updated",
      direction: "desc",
    });
    return issues.filter((i) => !i.pull_request);
  }

  function normalizeTitle(title) {
    return String(title || "")
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function hasExistingMarker(marker, openIssues) {
    return openIssues.some((issue) => String(issue.body || "").includes(marker));
  }

  function hasSimilarTitle(title, openIssues) {
    const target = normalizeTitle(title);
    return openIssues.some((issue) => {
      const existing = normalizeTitle(issue.title);
      return existing === target || existing.includes(target) || target.includes(existing);
    });
  }

  /**
   * Parse CodeRabbit --plain output into findings.
   *
   * This is intentionally tolerant because the CLI docs show plain text modes
   * but not a guaranteed JSON schema on the referenced page.
   */
  function parseFindings(text) {
    const lines = String(text || "").split(/\r?\n/);

    const findings = [];
    let current = null;

    const flush = () => {
      if (!current) return;
      const message = current.message.join("\n").trim();
      const file = current.file || "";
      const line = current.line || 1;

      if (message) {
        findings.push({
          file,
          line,
          summary: current.summary || inferSummary(message),
          details: message,
        });
      }
      current = null;
    };

    for (const line of lines) {
      // Common path:line signal
      const pathMatch = line.match(/([A-Za-z0-9_\-./\\]+\.[A-Za-z0-9]+):(\d+)/);
      // Bullet/header style line
      const bulletMatch = line.match(/^\s*[-*]\s+(.*)$/);

      if (pathMatch) {
        flush();
        current = {
          file: pathMatch[1].replaceAll("\\", "/"),
          line: Number(pathMatch[2]),
          summary: "",
          message: [line.trim()],
        };
        continue;
      }

      if (bulletMatch && !current) {
        current = {
          file: "",
          line: 1,
          summary: bulletMatch[1].trim(),
          message: [line.trim()],
        };
        continue;
      }

      if (current) {
        current.message.push(line);
      }
    }

    flush();
    return findings;
  }

  function inferSummary(text) {
    const firstSentence = String(text).split(/\n+/)[0].trim();
    return firstSentence.slice(0, 180);
  }

  function scoreFinding(finding) {
    const hay = normalizeText(
      [finding.file, finding.summary, finding.details].filter(Boolean).join(" ")
    );

    let score = 0;

    for (const kw of POSITIVE_KEYWORDS) {
      if (hay.includes(kw)) score += 2;
    }

    for (const kw of NEGATIVE_KEYWORDS) {
      if (hay.includes(kw)) score -= 4;
    }

    const file = normalizeText(finding.file);
    if (file.startsWith("docs/") || file.endsWith(".md") || file.endsWith(".rst")) score += 2;
    if (file.includes("test") || file.startsWith("tests/")) score += 2;
    if (file.startsWith(".github/workflows/")) score -= 1;

    // Prefer localized findings
    if (finding.file) score += 1;
    if (finding.line && finding.line > 0) score += 1;

    // Penalize broad/high-risk wording
    if (hay.includes("multiple files")) score -= 2;
    if (hay.includes("across the codebase")) score -= 3;
    if (hay.includes("architectural")) score -= 3;

    return score;
  }

  function isCandidate(finding) {
    return scoreFinding(finding) >= 3;
  }

  function buildIssueTitle(finding) {
    const file = finding.file || "repository";
    const summary = normalizeText(finding.summary);

    if (summary.includes("test")) {
      return `[GFI Candidate] Add or improve tests for ${file}`;
    }
    if (summary.includes("error")) {
      return `[GFI Candidate] Improve error handling clarity in ${file}`;
    }
    if (summary.includes("documentation") || summary.includes("readme") || summary.includes("docs")) {
      return `[GFI Candidate] Improve documentation in ${file}`;
    }
    if (summary.includes("type") || summary.includes("typing")) {
      return `[GFI Candidate] Improve typing in ${file}`;
    }
    if (summary.includes("validation")) {
      return `[GFI Candidate] Improve validation flow in ${file}`;
    }

    return `[GFI Candidate] Beginner-friendly improvement in ${file}`;
  }

  function buildIssueBody(finding, key) {
    const fileLine = finding.file ? `\`${finding.file}:${finding.line}\`` : "_Not provided by CLI output_";

    return [
      candidateMarker(key),
      "",
      "## Summary",
      finding.summary || "CodeRabbit CLI identified a localized improvement opportunity that appears suitable for a new contributor.",
      "",
      "## Why This Is a Good First Issue Candidate",
      "- The finding appears localized and actionable.",
      "- It does not appear to require a major redesign.",
      "- It is suitable for maintainer review before promotion to an official `good first issue`.",
      "",
      "## Source",
      "- Detector: `CodeRabbit CLI --plain`",
      `- Location: ${fileLine}`,
      "",
      "## CodeRabbit Finding",
      "```text",
      String(finding.details || "").slice(0, 4000),
      "```",
      "",
      "## Suggested Acceptance Criteria",
      "- [ ] Keep the change scoped to the affected file(s) or a small related area.",
      "- [ ] Fix the issue described in the finding.",
      "- [ ] Add or update tests if behavior changes.",
      "- [ ] Preserve existing behavior unless maintainers request otherwise.",
      "",
      "## Maintainer Notes",
      "- Review whether the issue is truly beginner-friendly.",
      "- Promote to `good first issue` only after confirming scope and clarity.",
      "",
      "_Generated automatically from a CodeRabbit CLI repository scan._",
    ].join("\n");
  }

  async function createIssueIfNeeded(finding) {
    const key = sha(`${finding.file}|${finding.line}|${finding.summary}|${finding.details}`);
    const marker = candidateMarker(key);
    const title = buildIssueTitle(finding);
    const body = buildIssueBody(finding, key);

    const openIssues = await getOpenIssues();

    if (hasExistingMarker(marker, openIssues)) {
      core.info(`Skipping ${key}: exact candidate already exists.`);
      return false;
    }

    if (hasSimilarTitle(title, openIssues)) {
      core.info(`Skipping ${key}: similar open issue title already exists.`);
      return false;
    }

    const created = await github.rest.issues.create({
      owner,
      repo,
      title,
      body,
      labels: [TARGET_LABEL],
    });

    core.info(`Created issue #${created.data.number}: ${title}`);
    return true;
  }

  await ensureLabelExists();

  const findings = parseFindings(rawOutput);
  core.info(`Parsed ${findings.length} raw CodeRabbit findings.`);

  const candidates = findings
    .filter(isCandidate)
    .sort((a, b) => scoreFinding(b) - scoreFinding(a))
    .slice(0, MAX_ISSUES_PER_RUN * 3);

  core.info(`Selected ${candidates.length} candidate findings after filtering.`);

  let createdCount = 0;
  let skippedCount = 0;

  for (const finding of candidates) {
    if (createdCount >= MAX_ISSUES_PER_RUN) break;

    try {
      const created = await createIssueIfNeeded(finding);
      if (created) createdCount += 1;
      else skippedCount += 1;
    } catch (error) {
      skippedCount += 1;
      core.warning(`Failed to create candidate issue: ${error?.message || String(error)}`);
    }
  }

  await core.summary
    .addHeading("Good First Issue Candidate Scan Summary")
    .addTable([
      [{ data: "Metric", header: true }, { data: "Value", header: true }],
      ["Raw CodeRabbit findings", String(findings.length)],
      ["Candidate findings considered", String(candidates.length)],
      ["Issues created", String(createdCount)],
      ["Skipped", String(skippedCount)],
      ["MAX_ISSUES_PER_RUN", String(MAX_ISSUES_PER_RUN)],
    ])
    .write();
};