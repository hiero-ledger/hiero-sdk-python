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
 * the three team roles. Returns empty sets for any role it can't parse, so
 * callers degrade to "no known members" rather than throwing.
 *
 * @param {string} [repoRoot] - Directory to read docs/team.md from.
 * @returns {{ triage: Set<string>, committer: Set<string>, maintainer: Set<string> }}
 */
function getTeamRoles(repoRoot = process.cwd()) {
    const filePath = path.join(repoRoot, "docs", "team.md");
    let contents;

    try {
        contents = fs.readFileSync(filePath, "utf8");
    } catch (err) {
        console.log(`Failed to read docs/team.md: ${err.message}`);
        return { triage: new Set(), committer: new Set(), maintainer: new Set() };
    }

    return {
        triage: extractSection(contents, SECTION_HEADINGS.triage),
        committer: extractSection(contents, SECTION_HEADINGS.committer),
        maintainer: extractSection(contents, SECTION_HEADINGS.maintainer),
    };
}

module.exports = { getTeamRoles };
