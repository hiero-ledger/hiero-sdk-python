const { PRIORITY_LABEL_NAMES, TYPE_LABEL_NAMES } = require('./constants');

/**
 * Extract priority and type label names from all issues linked in a PR body.
 *
 * Parses the body for closing keywords (closes, fixes, resolves) followed by
 * a #number reference.  Fetches each linked issue via the REST API and
 * collects its priority/type labels.
 *
 * @param {string} prBody   - Raw markdown body of the pull request
 * @param {object} octokit  - Octokit instance (github.rest)
 * @param {string} owner    - Repository owner
 * @param {string} repo     - Repository name
 * @returns {Promise<string[]>} Deduplicated array of matching label names
 */
async function getLinkedIssueLabels(prBody, octokit, owner, repo) {
    // Same closing-keyword regex as sync-issue-labels-compute.yml
    // NOTE: Matches same-repo "#123" references only. Cross-repo references
    // (owner/repo#123) and full GitHub URLs are intentionally not matched.
    const regex =
        /(?:fix|fixes|fixed|close|closes|closed|resolve|resolves|resolved)[:\s]+\s*#(\d+)\b/gi;

    const issueNumbers = new Set();
    let match;
    while ((match = regex.exec(prBody || '')) !== null) {
        issueNumbers.add(Number(match[1]));
    }

    if (issueNumbers.size === 0) {
        console.log('  No linked issues found in the PR body.');
        return [];
    }

    console.log(`  Linked issues: #${Array.from(issueNumbers).join(', #')}`);

    const discovered = new Set();

    for (const num of issueNumbers) {
        try {
            const { data: issue } = await octokit.rest.issues.get({
                owner,
                repo,
                issue_number: num,
            });

            // Skip if the "issue" is actually a pull request
            if (issue.pull_request) {
                console.log(`  Skipping #${num} — it is a PR, not an issue.`);
                continue;
            }

            const names = (issue.labels || []).map((l) =>
                typeof l === 'string' ? l : l.name
            );

            for (const name of names) {
                const lower = name.toLowerCase();
                if (PRIORITY_LABEL_NAMES.has(lower) || TYPE_LABEL_NAMES.has(lower)) {
                    discovered.add(name);
                }
            }

            console.log(
                `  Issue #${num} labels filtered to: [${Array.from(discovered).join(', ')}]`
            );
        } catch (error) {
            // Log and continue — a single unreachable issue should not abort the run
            const message = error instanceof Error ? error.message : String(error);
            console.log(`  ⚠ Could not fetch issue #${num}: ${message}`);
        }
    }

    return Array.from(discovered);
}

module.exports = { getLinkedIssueLabels };
