/**
 * Team roles — static source of truth for triage/committer/maintainer
 * identification.
 *
 * Parses docs/team.md, which already lists all three Hiero Python SDK team
 * roles with their GitHub IDs. Using this instead of
 * review-sync/helpers/permissions.js's getCollaboratorPermissionLevel calls
 * means role lookups here stay free of extra API calls: docs/team.md is
 * already the project's own curated, human-maintained roster.
 *
 * (See PR #2503 review discussion — this replaces an earlier, narrower
 * version of this file that only covered maintainers via MAINTAINERS.md,
 * once it turned out docs/team.md already covers triage and committer too.)
 */

const fs = require("fs");
const path = require("path");

// Matches a "| Name | @githubId |" row and captures the GitHub ID cell.
const TABLE_ROW = /^\|\s*[^|]+\|\s*@?([A-Za-z0-9-]+)\s*\|/;

const SECTION_HEADINGS = {
    triage: "## Triage Members",
    committer: "## Committer Members",
    maintainer: "## Maintainer Members",
};

/**
 * Pulls the GitHub IDs out of one section of docs/team.md (from its
 * heading up to the next "## " heading or end of file).
 *
 * @param {string} contents - Full text of docs/team.md.
 * @param {string} heading - Section heading to extract, e.g. "## Triage Members".
 * @returns {Set<string>} - Lowercased GitHub IDs.
 */
function extractSection(contents, heading) {
    const afterHeading = contents.split(heading)[1];
    if (!afterHeading) return new Set();

    const sectionBody = afterHeading.split(/\n##\s/)[0];
    const logins = new Set();

    for (const line of sectionBody.split("\n")) {
        const match = TABLE_ROW.exec(line);
        if (!match) continue;

        const githubId = match[1].trim();
        if (!githubId || githubId === "GitHub-ID" || /^-+$/.test(githubId)) {
            continue;
        }

        logins.add(githubId.toLowerCase());
    }

    return logins;
}

/**
 * Reads docs/team.md and returns the GitHub IDs (lowercased) for each of
 * the three team roles, plus whether the roster is usable.
 *
 * `available` is false when the file can't be read, AND when it reads fine
 * but yields no maintainers. A valid roster always has maintainers, so an
 * empty maintainer set means the file's headings/format have drifted from
 * what this parser expects (e.g. "## Maintainer Members" was renamed) —
 * without this check, such drift would silently make every approval look
 * unqualified and report every PR as "waiting on committer, maintainer"
 * forever, which is indistinguishable from a genuinely-early review state.
 *
 * Callers MUST check `available` before treating empty sets as "nobody
 * holds this role" (see review-status-evaluator.js's ROSTER_UNAVAILABLE
 * handling). On failure the role sets carry whatever could be parsed
 * (possibly empty) for debuggability.
 *
 * @param {string} [repoRoot] - Directory to read docs/team.md from.
 * @returns {{
 *   available: boolean,
 *   triage: Set<string>,
 *   committer: Set<string>,
 *   maintainer: Set<string>,
 * }}
 */
function getTeamRoles(repoRoot = process.cwd()) {
    const filePath = path.join(repoRoot, "docs", "team.md");
    let contents;

    try {
        contents = fs.readFileSync(filePath, "utf8");
    } catch (err) {
        console.log(`Failed to read docs/team.md: ${err.message}`);
        return {
            available: false,
            triage: new Set(),
            committer: new Set(),
            maintainer: new Set(),
        };
    }

    const roles = {
        available: true,
        triage: extractSection(contents, SECTION_HEADINGS.triage),
        committer: extractSection(contents, SECTION_HEADINGS.committer),
        maintainer: extractSection(contents, SECTION_HEADINGS.maintainer),
    };

    if (roles.maintainer.size === 0) {
        console.log(
            `docs/team.md was read but no maintainers were parsed — the file's ` +
                `headings/format have likely drifted from what team-roles.js expects ` +
                `("${SECTION_HEADINGS.maintainer}" table of "| Name | @GitHub-ID |" rows). ` +
                `Treating the roster as unavailable rather than misreporting review status.`
        );
        roles.available = false;
    }

    return roles;
}

module.exports = { getTeamRoles };
