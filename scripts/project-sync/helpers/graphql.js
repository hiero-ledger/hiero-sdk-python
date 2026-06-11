
/**
 * Add a PR (by its node ID) to a GitHub Projects V2 board.
 *
 * Idempotent: if the PR is already on the board GitHub returns the existing
 * item node ID unchanged.
 *
 * @param {object} github    - Octokit instance with .graphql() support
 * @param {string} projectId - Global node ID of the project (e.g. "PVT_...")
 * @param {string} contentId - Global node ID of the PR (e.g. "PR_...")
 * @returns {Promise<string>} The item node ID on the project board
 */
async function addItemToProject(github, projectId, contentId) {
    const result = await github.graphql(
        `
    mutation AddItemToProject($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: { projectId: $projectId, contentId: $contentId }) {
        item {
          id
        }
      }
    }
  `,
        { projectId, contentId }
    );

    return result.addProjectV2ItemById.item.id;
}

/**
 * Set a Single Select field on a project item.
 *
 * No-op-safe: GitHub accepts an update to the value already set without error.
 *
 * @param {object} github    - Octokit instance with .graphql() support
 * @param {string} projectId - Global node ID of the project
 * @param {string} itemId    - Node ID of the item on the project board
 * @param {string} fieldId   - Node ID of the Single Select field
 * @param {string} optionId  - Node ID of the option to select
 * @returns {Promise<void>}
 */
async function updateSingleSelectField(github, projectId, itemId, fieldId, optionId) {
    await github.graphql(
        `
    mutation UpdateField($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
      updateProjectV2ItemFieldValue(input: {
        projectId: $projectId,
        itemId: $itemId,
        fieldId: $fieldId,
        value: { singleSelectOptionId: $optionId }
      }) {
        projectV2Item {
          id
        }
      }
    }
  `,
        { projectId, itemId, fieldId, optionId }
    );
}

/**
 * Fetch all Single Select fields and their options for a project.
 *
 * Returns a map of fieldName → { id, options: { optionName → optionId } }.
 * Non-SingleSelect fields (text, date, number…) are silently skipped because
 * the GraphQL inline fragment only matches ProjectV2SingleSelectField.
 *
 * @param {object} github    - Octokit instance with .graphql() support
 * @param {string} projectId - Global node ID of the project
 * @returns {Promise<Record<string, { id: string, options: Record<string, string> }>>}
 */
async function fetchProjectFields(github, projectId) {
    const result = await github.graphql(
        `
    query FetchFields($projectId: ID!) {
      node(id: $projectId) {
        ... on ProjectV2 {
          fields(first: 50) {
            nodes {
              ... on ProjectV2SingleSelectField {
                id
                name
                options {
                  id
                  name
                }
              }
            }
          }
        }
      }
    }
  `,
        { projectId }
    );

    const fieldMap = {};
    for (const node of result.node.fields.nodes) {
        // Non-SingleSelect fields have no .name at this fragment type — skip them
        if (!node.name) continue;

        const options = {};
        for (const opt of node.options || []) {
            options[opt.name] = opt.id;
        }
        fieldMap[node.name] = { id: node.id, options };
    }

    return fieldMap;
}

module.exports = { addItemToProject, updateSingleSelectField, fetchProjectFields };
