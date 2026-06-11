
const helpers = require('./helpers');
const { PROJECT_NODE_ID } = helpers.constants;
const { addItemToProject, updateSingleSelectField, fetchProjectFields } = helpers.graphql;
const { ensureAllLabels } = helpers.labels;

module.exports = async ({ github, context, core }) => {
    const dryRun = (process.env.DRY_RUN || 'false').toLowerCase() === 'true';
    const { owner, repo } = context.repo;

    if (dryRun) {
        console.log('=== DRY RUN MODE — no project fields will be modified ===\n');
    }

    // ── 1. Validate required config ──────────────────────────────────────────
    if (!PROJECT_NODE_ID) {
        core.setFailed(
            'PROJECT_NODE_ID is not set. Export it as an environment variable or ' +
            'set the default in helpers/constants.js.'
        );
        return;
    }

    // ── 2. Ensure managed labels exist ───────────────────────────────────────
    console.log('--- Ensuring Labels Exist ---');
    await ensureAllLabels(github, owner, repo, dryRun);

    // ── 3. Fetch live field metadata from the board ───────────────────────────
    //
    // We resolve field and option IDs at runtime rather than hardcoding them.
    // This means the scripts continue to work if the project is recreated.
    console.log('\n--- Fetching Project Fields ---');
    const fields = await fetchProjectFields(github, PROJECT_NODE_ID);
    console.log(`  Resolved fields: ${Object.keys(fields).join(', ')}`);

    const priorityField = fields['Priority'];
    const typeField = fields['Type'];

    if (!priorityField) {
        console.log("  ⚠ 'Priority' field not found on the project board. Skipping priority sync.");
    }
    if (!typeField) {
        console.log("  ⚠ 'Type' field not found on the project board. Skipping type sync.");
    }

    return async ({ prNodeId, priority, type }) => {
        console.log(`\n--- Syncing PR node: ${prNodeId} ---`);
        console.log(`  priority="${priority || 'none'}"  type="${type || 'none'}"`);

        // ── 4. Add PR to the board (idempotent) ────────────────────────────────
        if (dryRun) {
            console.log(`  [DRY RUN] Would add PR ${prNodeId} to project ${PROJECT_NODE_ID}.`);
        } else {
            const itemId = await addItemToProject(github, PROJECT_NODE_ID, prNodeId);
            console.log(`  Item node ID on board: ${itemId}`);

            // ── 5. Update Priority field ──────────────────────────────────────────
            if (priority && priorityField) {
                const optionId = priorityField.options[priority];
                if (optionId) {
                    await updateSingleSelectField(
                        github, PROJECT_NODE_ID, itemId, priorityField.id, optionId
                    );
                    console.log(`  + Set Priority → "${priority}"`);
                } else {
                    console.log(`  ⚠ Priority option "${priority}" not found on board. Skipping.`);
                }
            }

            // ── 5. Update Type field ──────────────────────────────────────────────
            if (type && typeField) {
                const optionId = typeField.options[type];
                if (optionId) {
                    await updateSingleSelectField(
                        github, PROJECT_NODE_ID, itemId, typeField.id, optionId
                    );
                    console.log(`  + Set Type → "${type}"`);
                } else {
                    console.log(`  ⚠ Type option "${type}" not found on board. Skipping.`);
                }
            }
        }
    };
};
