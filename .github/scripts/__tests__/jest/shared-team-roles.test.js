// __tests__/jest/shared-team-roles.test.js
//
// Run from .github/scripts:
// npm run test:js -- shared-team-roles.test.js
//
// Exercises the real getTeamRoles() against fixture docs/team.md files in
// temp directories (review-status-evaluator.test.js mocks this module, so
// the parsing itself is only covered here).

const fs = require('fs');
const os = require('os');
const path = require('path');

const { getTeamRoles } = require('../../shared/team-roles');

const VALID_ROSTER = `# Hiero Python SDK Team

## Triage Members

| Name | GitHub ID |
| :--- | :--- |
| Alice Example | @Alice |
| carol | @carol |

## Committer Members

| Name | GitHub ID |
| :--- | :--- |
| Bob Example | @bob-example |

## Maintainer Members

| Name | GitHub ID |
| :--- | :--- |
| Mallory Maintainer | @Mallory |
`;

function writeRosterFixture(contents) {
    const repoRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'team-roles-'));
    fs.mkdirSync(path.join(repoRoot, 'docs'));

    if (contents !== null) {
        fs.writeFileSync(path.join(repoRoot, 'docs', 'team.md'), contents);
    }

    return repoRoot;
}

describe('team-roles.js — getTeamRoles', () => {
    test('parses all three sections from a valid roster, lowercasing IDs', () => {
        const roles = getTeamRoles(writeRosterFixture(VALID_ROSTER));

        expect(roles.available).toBe(true);
        expect([...roles.triage].sort()).toEqual(['alice', 'carol']);
        expect([...roles.committer]).toEqual(['bob-example']);
        expect([...roles.maintainer]).toEqual(['mallory']);
    });

    test('reports unavailable when docs/team.md is missing', () => {
        const roles = getTeamRoles(writeRosterFixture(null));

        expect(roles.available).toBe(false);
        expect(roles.maintainer.size).toBe(0);
    });

    test('reports unavailable when the maintainer heading has drifted', () => {
        // A renamed heading parses "successfully" to an empty maintainer
        // set; without the zero-maintainer guard this would misreport every
        // PR as waiting on committer+maintainer forever.
        const drifted = VALID_ROSTER.replace('## Maintainer Members', '## Maintainer Team');

        const roles = getTeamRoles(writeRosterFixture(drifted));

        expect(roles.available).toBe(false);
    });

    test('reports unavailable when the maintainer table has no rows', () => {
        const emptyMaintainers = VALID_ROSTER.replace(
            /## Maintainer Members[\s\S]*$/,
            '## Maintainer Members\n\n| Name | GitHub ID |\n| :--- | :--- |\n'
        );

        const roles = getTeamRoles(writeRosterFixture(emptyMaintainers));

        expect(roles.available).toBe(false);
    });

    test('stays available when only a non-maintainer section is empty', () => {
        // Triage drift degrades gracefully (committer/maintainer approvals
        // still qualify for the triage gate), so it must not take the whole
        // roster offline.
        const noTriage = VALID_ROSTER.replace('## Triage Members', '## Triage Team');

        const roles = getTeamRoles(writeRosterFixture(noTriage));

        expect(roles.available).toBe(true);
        expect(roles.triage.size).toBe(0);
        expect([...roles.maintainer]).toEqual(['mallory']);
    });

    test('skips separator and header rows rather than treating them as IDs', () => {
        const roles = getTeamRoles(writeRosterFixture(VALID_ROSTER));

        expect(roles.triage.has('github-id')).toBe(false);
        expect(roles.triage.has('---')).toBe(false);
    });
});
