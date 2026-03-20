const fs = require('fs');
const { execSync } = require('child_process');

module.exports = async ({ github, context, core }) => {
  const dryRun = context.payload.inputs?.dry_run === 'true' || false;
  const prNumber = context.payload.inputs?.pr_number || context.payload.pull_request?.number;

  if (!prNumber) {
    core.setFailed('PR number required for workflow_dispatch');
    return;
  }

  const { data: pr } = await github.rest.pulls.get({
    owner: context.repo.owner,
    repo: context.repo.repo,
    pull_number: prNumber,
  });

  const title = pr.title.trim();
  const branch = pr.head.ref;

  core.info(`Processing PR #${prNumber}: ${title} (${branch})`);

  const match = title.match(/^Bump ([^ ]+(?:\/[^ ]+)*) from ([^ ]+) to ([^ ]+)(?: in .*)?$/);
  if (!match) {
    core.info('Not a Dependabot bump PR — skipping');
    return;
  }

  const [, pkg, oldVer, newVer] = match;
  const entry = `chore: bump ${pkg} from ${oldVer} to ${newVer} (#${prNumber})`;

  const section = branch.startsWith('dependabot/github-actions/')
    ? '.github'
    : 'Src';
  core.info(`Entry: ${entry} under ${section}`);

  if (dryRun) {
    core.info('[DRY-RUN] Would update CHANGELOG.md');
    return;
  }

  const changelogPath = 'CHANGELOG.md';
  let lines = fs.readFileSync(changelogPath, 'utf8').split('\n');

  let unreleasedIndex = -1;
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim() === '## [Unreleased]') {
      unreleasedIndex = i;
      break;
    }
  }

  if (unreleasedIndex === -1) {
    core.info('Inserting missing ## [Unreleased] at top');
    lines.unshift('## [Unreleased]', '');
    unreleasedIndex = 0;
  }

  let sectionIndex = -1;
  for (let i = unreleasedIndex + 1; i < lines.length; i++) {
    const trimmed = lines[i].trim();
    if (trimmed.startsWith('## ')) break;
    if (trimmed === `### ${section}`) {
      sectionIndex = i;
      break;
    }
  }

  if (sectionIndex === -1) {
    let pos = unreleasedIndex + 1;
    while (pos < lines.length && lines[pos].trim() === '') pos++;
    lines.splice(pos, 0, `### ${section}`, '');
    sectionIndex = pos;
  }

  let insertPos = sectionIndex + 1;
  while (insertPos < lines.length && lines[insertPos].trim() === '') insertPos++;

  const entryLine = `- ${entry}`;
  if (lines.slice(insertPos, insertPos + 10).some(l => l.includes(entry))) {
    core.info('Entry already present — skipping');
  } else {
    lines.splice(insertPos, 0, entryLine);
    core.info(`Inserted entry under ${section}`);
  }

  fs.writeFileSync(changelogPath, lines.join('\n'));
  core.info('CHANGELOG.md updated');

  execSync('git config user.name "github-actions[bot]"');
  execSync('git config user.email "41898282+github-actions[bot]@users.noreply.github.com"');
  execSync('git add CHANGELOG.md');
  try {
    const commitOutput = execSync(
      `git commit -S -s -m "chore: update CHANGELOG for Dependabot bump (#${prNumber})" --signoff`,
      { stdio: 'pipe' }
    );
    const commitMsg = commitOutput.toString().trim() || '(commit succeeded, no output)';
    core.info(`Commit created: ${commitMsg}`);

    // Push
    execSync(`git push origin HEAD:${pr.head.ref}`, { stdio: 'pipe' });
    core.info(`Pushed CHANGELOG update to branch ${pr.head.ref}`);
  } catch (e) {
    const errMsg = e.message || String(e);

    // Handle the common "nothing to commit" cases gracefully
    if (
      errMsg.includes('nothing to commit') ||
      errMsg.includes('working tree clean') ||
      errMsg.includes('no changes added to commit')
    ) {
      core.info('No CHANGELOG changes to commit (already up-to-date)');
    } else {
      core.warning(`Git commit/push failed (non-fatal): ${errMsg}`);
    }
  }

  // Assignee
  const assignee = process.env.DEPENDABOT_ASSIGNEE;
  if (assignee) {
    try {
      await github.rest.issues.addAssignees({
        owner: context.repo.owner,
        repo: context.repo.repo,
        issue_number: prNumber,
        assignees: [assignee],
      });
      core.info(`Assigned ${assignee} to PR #${prNumber}`);
    } catch (err) {
      core.warning(`Assignee step failed: ${err.message}`);
    }
  } else {
    core.warning('No DEPENDABOT_ASSIGNEE env var set — skipping assignment');
  }
};