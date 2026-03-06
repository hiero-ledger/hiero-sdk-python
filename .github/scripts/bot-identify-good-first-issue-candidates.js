// Repository-wide scanner that discovers beginner-friendly tasks and creates
// candidate GitHub issues for maintainer review.

const fs = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');

module.exports = async ({ github, context, core }) => {
  const owner = context.repo.owner;
  const repo = context.repo.repo;
  const repoRoot = process.cwd();

  const TARGET_LABEL = 'Good First Issue Candidate';
  const TARGET_LABEL_DESCRIPTION =
    'AI-identified issue that may be suitable for new contributors. Requires maintainer review.';
  const TARGET_LABEL_COLOR = 'C2E0C6';

  const MAX_ISSUES_PER_RUN = clampInt(process.env.MAX_ISSUES_PER_RUN, 5, 1, 20);
  const MAX_FILES_TO_SCAN = clampInt(process.env.MAX_FILES_TO_SCAN, 1800, 200, 4000);
  const MAX_FILE_SIZE_BYTES = clampInt(process.env.MAX_FILE_SIZE_BYTES, 240000, 10000, 1000000);

  const ALLOWED_EXTENSIONS = new Set([
    '.py',
    '.md',
    '.rst',
    '.txt',
    '.yml',
    '.yaml',
    '.js',
    '.ts',
    '.tsx',
    '.jsx',
    '.json',
  ]);

  const IGNORED_DIRS = new Set([
    '.git',
    '.github/archive',
    '.venv',
    'venv',
    '__pycache__',
    '.mypy_cache',
    '.pytest_cache',
    'node_modules',
    'dist',
    'build',
    'site-packages',
    '.idea',
    '.vscode',
    '.ruff_cache',
  ]);

  const RISK_KEYWORDS = [
    'security',
    'vulnerability',
    'auth',
    'authentication',
    'authorization',
    'cryptography',
    'consensus',
    'architecture',
    'redesign',
    'breaking change',
    'performance-critical',
    'throughput',
    'latency',
    'protocol rewrite',
  ];

  const WEAK_ERROR_MESSAGES = new Set([
    'error',
    'failed',
    'failure',
    'invalid',
    'bad input',
    'bad request',
    'exception',
    'unknown error',
  ]);

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

  function isIgnored(relPath) {
    const normalized = relPath.replaceAll('\\', '/');
    return [...IGNORED_DIRS].some((d) => normalized === d || normalized.startsWith(`${d}/`));
  }

  async function walkFiles(rootDir) {
    const out = [];
    const stack = [''];

    while (stack.length > 0 && out.length < MAX_FILES_TO_SCAN) {
      const rel = stack.pop();
      const abs = path.join(rootDir, rel);

      let entries;
      try {
        entries = await fs.readdir(abs, { withFileTypes: true });
      } catch {
        continue;
      }

      for (const entry of entries) {
        const childRel = rel ? path.posix.join(rel.replaceAll('\\', '/'), entry.name) : entry.name;
        if (isIgnored(childRel)) continue;

        if (entry.isDirectory()) {
          stack.push(childRel);
          continue;
        }

        if (!entry.isFile()) continue;

        const ext = path.extname(entry.name).toLowerCase();
        if (!ALLOWED_EXTENSIONS.has(ext)) continue;

        const childAbs = path.join(rootDir, childRel);
        try {
          const stat = await fs.stat(childAbs);
          if (stat.size > MAX_FILE_SIZE_BYTES) continue;
        } catch {
          continue;
        }

        out.push(childRel);
        if (out.length >= MAX_FILES_TO_SCAN) break;
      }
    }

    return out;
  }

  function findLineNumber(content, idx) {
    let line = 1;
    for (let i = 0; i < idx && i < content.length; i += 1) {
      if (content[i] === '\n') line += 1;
    }
    return line;
  }

  function hasRiskSignals(...texts) {
    const merged = texts.join(' ').toLowerCase();
    return RISK_KEYWORDS.some((kw) => merged.includes(kw));
  }

  function makeCandidateKey(rule, relPath, line, snippet) {
    return crypto
      .createHash('sha1')
      .update(`${rule}|${relPath}|${line}|${snippet}`)
      .digest('hex')
      .slice(0, 14);
  }

  function markerForCandidate(key) {
    return `<!-- gfi-candidate-key:${key} -->`;
  }

  function classifyPath(relPath) {
    const normalized = String(relPath || '').replaceAll('\\', '/').toLowerCase();
    if (normalized.startsWith('docs/') || normalized.endsWith('.md') || normalized.endsWith('.rst')) {
      return 'docs';
    }
    if (normalized.startsWith('.github/workflows/') || normalized.includes('/workflows/')) {
      return 'workflows';
    }
    return 'code';
  }

  function issueTitleFor(candidate) {
    const primaryFile = candidate.files[0];
    const pathClass = classifyPath(primaryFile);

    switch (candidate.rule) {
      case 'todo_actionable':
        if (pathClass === 'docs') {
          return `[GFI Candidate] Fill actionable documentation gap in ${primaryFile}`;
        }
        if (pathClass === 'workflows') {
          return `[GFI Candidate] Improve workflow maintainability in ${primaryFile}`;
        }
        return `[GFI Candidate] Resolve actionable TODO in ${primaryFile}`;
      case 'weak_error_message':
        return `[GFI Candidate] Improve error message clarity in ${primaryFile}`;
      case 'missing_tests':
        return `[GFI Candidate] Add focused tests for ${candidate.modulePath}`;
      case 'typing_improvement':
        return `[GFI Candidate] Add return type hints in ${primaryFile}`;
      case 'validation_inconsistency':
        return `[GFI Candidate] Clarify validation flow in ${primaryFile}`;
      default:
        if (pathClass === 'docs') {
          return `[GFI Candidate] Beginner-friendly docs improvement in ${primaryFile}`;
        }
        if (pathClass === 'workflows') {
          return `[GFI Candidate] Beginner-friendly workflow improvement in ${primaryFile}`;
        }
        return `[GFI Candidate] Beginner-friendly improvement in ${primaryFile}`;
    }
  }

  function issueBodyFor(candidate, key) {
    const filesBlock = candidate.files.map((f) => `- \`${f}\``).join('\n');
    const criteriaBlock = candidate.acceptanceCriteria.map((c) => `- [ ] ${c}`).join('\n');
    const whyBlock = candidate.whyBeginnerFriendly;

    return [
      markerForCandidate(key),
      '',
      `## Summary`,
      candidate.summary,
      '',
      `## Why This Is Beginner-Friendly`,
      whyBlock,
      '',
      `## Likely Affected Files`,
      filesBlock,
      '',
      `## Evidence`,
      `- Rule: \`${candidate.rule}\``,
      `- Location: \`${candidate.files[0]}:${candidate.line}\``,
      `- Snippet: \`${candidate.snippet.slice(0, 220)}\``,
      '',
      `## Acceptance Criteria`,
      criteriaBlock,
      '',
      `## Safety Notes`,
      '- Keep scope localized to listed files/directories.',
      '- Avoid architectural/API redesign or broad refactors.',
      '- If work expands significantly, split into a new follow-up issue.',
      '',
      '_Generated by automated repository scan for maintainer review._',
    ].join('\n');
  }

  function buildTodoCandidate(relPath, line, text) {
    return {
      rule: 'todo_actionable',
      files: [relPath],
      line,
      snippet: text.trim(),
      score: 3,
      summary: `Address an actionable TODO/FIXME comment found in \`${relPath}\`.`,
      whyBeginnerFriendly:
        'The task appears localized, has concrete intent, and can be completed in a single small change set.',
      acceptanceCriteria: [
        'Implement the TODO/FIXME action in the identified file.',
        'Update or remove the TODO/FIXME comment once addressed.',
        'Add or adjust tests if behavior changes.',
      ],
    };
  }

  function buildWeakErrorCandidate(relPath, line, message, snippet) {
    return {
      rule: 'weak_error_message',
      files: [relPath],
      line,
      snippet,
      score: 3,
      summary: `Improve a weak error message (currently \`${message}\`) in \`${relPath}\`.`,
      whyBeginnerFriendly:
        'This is a low-risk quality improvement in a localized code path with clear expected output.',
      acceptanceCriteria: [
        'Replace the generic error text with a specific, user-actionable message.',
        'Preserve existing exception type unless maintainers request otherwise.',
        'Add or update a test assertion for the improved message where practical.',
      ],
    };
  }

  function buildTypingCandidate(relPath, line, snippet) {
    return {
      rule: 'typing_improvement',
      files: [relPath],
      line,
      snippet,
      score: 2,
      summary: `Add missing return type annotations to small function group in \`${relPath}\`.`,
      whyBeginnerFriendly:
        'Type hint additions are incremental, localized, and have clear completion criteria.',
      acceptanceCriteria: [
        'Add return type annotations for the targeted untyped functions.',
        'Keep behavior unchanged.',
        'Ensure static analysis (mypy/pylance) stays clean for touched code.',
      ],
    };
  }

  function buildValidationCandidate(relPath, line, snippet) {
    return {
      rule: 'validation_inconsistency',
      files: [relPath],
      line,
      snippet,
      score: 2,
      summary: `Clarify or harden a silent validation path in \`${relPath}\`.`,
      whyBeginnerFriendly:
        'The work is small and focused on making validation behavior explicit and consistent.',
      acceptanceCriteria: [
        'Replace silent fallback/pass behavior with explicit handling.',
        'Document expected behavior in code comments or docstring if needed.',
        'Add a test that covers the validation branch.',
      ],
    };
  }

  function buildMissingTestsCandidate(modulePath, suggestedTestsPath) {
    return {
      rule: 'missing_tests',
      files: [modulePath, suggestedTestsPath],
      modulePath,
      line: 1,
      snippet: `No obvious test module found for ${modulePath}`,
      score: 4,
      summary: `Create focused tests for \`${modulePath}\` under \`${suggestedTestsPath}\`.`,
      whyBeginnerFriendly:
        'Adding targeted tests is usually low-risk and helps new contributors learn behavior safely.',
      acceptanceCriteria: [
        `Add a new test file under \`${suggestedTestsPath}\` (or nearest existing test location).`,
        'Cover at least one success path and one edge/error path.',
        'Keep production code changes minimal and test-focused.',
      ],
    };
  }

  function isCandidateSafe(candidate) {
    if (!candidate || !candidate.files || candidate.files.length === 0) return false;
    if (candidate.files.length > 3) return false;
    if (hasRiskSignals(candidate.summary, candidate.snippet, ...candidate.files)) return false;
    return true;
  }

  async function extractCandidatesFromFile(relPath) {
    const abs = path.join(repoRoot, relPath);
    let content;
    try {
      content = await fs.readFile(abs, 'utf8');
    } catch {
      return [];
    }

    const out = [];

    // 1) Actionable TODO/FIXME markers.
    const lines = content.split(/\r?\n/);
    for (let i = 0; i < lines.length; i += 1) {
      const line = lines[i];
      const todoMatch = line.match(/\b(TODO|FIXME)\b\s*[:\-]?\s*(.+)/i);
      if (!todoMatch) continue;
      const details = (todoMatch[2] || '').trim();
      if (details.length < 12) continue;
      if (hasRiskSignals(details, relPath)) continue;
      out.push(buildTodoCandidate(relPath, i + 1, line));
    }

    // 2) Weak/unclear error messages in Python/JS/TS.
    const weakErrorRegexes = [
      /raise\s+(?:ValueError|RuntimeError|Exception|TypeError)\((['"`])([^'"`]{0,100})\1\)/g,
      /throw\s+new\s+(?:Error|TypeError|RangeError)\((['"`])([^'"`]{0,100})\1\)/g,
    ];

    for (const regex of weakErrorRegexes) {
      let match;
      while ((match = regex.exec(content)) !== null) {
        const message = String(match[2] || '').trim().toLowerCase();
        const isWeak = message.length < 12 || WEAK_ERROR_MESSAGES.has(message);
        if (!isWeak) continue;
        const line = findLineNumber(content, match.index);
        const snippet = String(match[0] || '').trim();
        if (hasRiskSignals(snippet, relPath)) continue;
        out.push(buildWeakErrorCandidate(relPath, line, message || 'generic error', snippet));
      }
    }

    // 3) Localized typing improvements for Python files.
    if (relPath.endsWith('.py')) {
      const untypedDefRegex = /^\s*def\s+([A-Za-z_]\w*)\([^)]*\)\s*:\s*$/gm;
      const typedDefRegex = /^\s*def\s+[A-Za-z_]\w*\([^)]*\)\s*->\s*[^:]+:\s*$/gm;
      const untyped = [...content.matchAll(untypedDefRegex)];
      const typed = [...content.matchAll(typedDefRegex)];

      if (untyped.length >= 2 && typed.length >= 1) {
        const m = untyped[0];
        const line = findLineNumber(content, m.index || 0);
        out.push(buildTypingCandidate(relPath, line, String(m[0] || '').trim()));
      }

      // 4) Validation inconsistency heuristic (silent pass/return on invalid path).
      const validationRegex = /if\s+.+:\s*(?:#.*)?\n\s*(?:pass|return\s+None)\b/gm;
      const valMatch = validationRegex.exec(content);
      if (valMatch) {
        const line = findLineNumber(content, valMatch.index || 0);
        const snippet = String(valMatch[0] || '').replace(/\s+/g, ' ').trim();
        if (!hasRiskSignals(snippet, relPath)) {
          out.push(buildValidationCandidate(relPath, line, snippet));
        }
      }
    }

    return out;
  }

  function suggestTestPath(modulePath) {
    const fileName = path.basename(modulePath, '.py');
    return `tests/unit/test_${fileName}.py`;
  }

  function buildMissingTestsCandidates(allFiles) {
    const out = [];
    const srcPy = allFiles.filter((f) => f.startsWith('src/') && f.endsWith('.py') && !f.endsWith('__init__.py'));
    const testFiles = new Set(allFiles.filter((f) => f.startsWith('tests/') && f.endsWith('.py')).map((f) => path.basename(f)));

    for (const modulePath of srcPy) {
      const fileStem = path.basename(modulePath, '.py');
      const directTest = `test_${fileStem}.py`;
      if (testFiles.has(directTest)) continue;

      const suggested = suggestTestPath(modulePath);
      out.push(buildMissingTestsCandidate(modulePath, suggested));
      if (out.length >= 6) break; // Avoid flooding candidates from this rule.
    }

    return out;
  }

  async function getOpenIssues() {
    const issues = await github.paginate(github.rest.issues.listForRepo, {
      owner,
      repo,
      state: 'open',
      per_page: 100,
      sort: 'updated',
      direction: 'desc',
    });
    return issues.filter((i) => !i.pull_request);
  }

  function normalizeTitle(title) {
    return String(title || '')
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function looksLikeSimilarOpenIssue(candidateTitle, openIssues) {
    const target = normalizeTitle(candidateTitle);
    return openIssues.some((issue) => {
      const existing = normalizeTitle(issue.title);
      return existing === target || existing.includes(target) || target.includes(existing);
    });
  }

  function hasExistingMarker(marker, openIssues) {
    return openIssues.some((issue) => String(issue.body || '').includes(marker));
  }

  async function createCandidateIssue(candidate, key) {
    const title = issueTitleFor(candidate);
    const body = issueBodyFor(candidate, key);
    const marker = markerForCandidate(key);

    const openIssues = await getOpenIssues();
    if (hasExistingMarker(marker, openIssues)) {
      core.info(`Skipping ${key}: exact marker already exists in an open issue.`);
      return false;
    }
    if (looksLikeSimilarOpenIssue(title, openIssues)) {
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

    core.info(`Created candidate issue #${created.data.number} for ${candidate.files[0]}`);
    return true;
  }

  await ensureLabelExists();

  const files = await walkFiles(repoRoot);
  core.info(`Scanning ${files.length} repository files for beginner-friendly candidate tasks.`);

  const rawCandidates = [];
  for (const relPath of files) {
    const extracted = await extractCandidatesFromFile(relPath);
    for (const candidate of extracted) {
      if (isCandidateSafe(candidate)) rawCandidates.push(candidate);
    }
  }

  // Repository-level scan signal: missing focused tests for source modules.
  const missingTestsCandidates = buildMissingTestsCandidates(files).filter(isCandidateSafe);
  rawCandidates.push(...missingTestsCandidates);

  // Deduplicate and sort strongest-first.
  const unique = new Map();
  for (const c of rawCandidates) {
    const key = makeCandidateKey(c.rule, c.files[0], c.line, c.snippet);
    if (!unique.has(key)) unique.set(key, { key, candidate: c });
  }

  const prioritized = [...unique.values()]
    .sort((a, b) => b.candidate.score - a.candidate.score)
    .slice(0, 40);

  let createdCount = 0;
  let skippedCount = 0;

  for (const item of prioritized) {
    if (createdCount >= MAX_ISSUES_PER_RUN) {
      core.warning(`Reached MAX_ISSUES_PER_RUN=${MAX_ISSUES_PER_RUN}. Stopping creation.`);
      break;
    }

    try {
      const created = await createCandidateIssue(item.candidate, item.key);
      if (created) createdCount += 1;
      else skippedCount += 1;
    } catch (error) {
      skippedCount += 1;
      core.warning(`Failed candidate ${item.key}: ${error?.message || String(error)}`);
    }
  }

  await core.summary
    .addHeading('Good First Issue Candidate Scan Summary')
    .addTable([
      [{ data: 'Metric', header: true }, { data: 'Value', header: true }],
      ['Files scanned', String(files.length)],
      ['Raw candidates found', String(rawCandidates.length)],
      ['Unique candidates considered', String(prioritized.length)],
      ['Issues created', String(createdCount)],
      ['Skipped/duplicates/errors', String(skippedCount)],
      ['MAX_ISSUES_PER_RUN', String(MAX_ISSUES_PER_RUN)],
    ])
    .write();
};
