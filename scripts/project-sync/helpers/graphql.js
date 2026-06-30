async function addItemToProject(github, projectId, contentId) {
  const result = await github.graphql(`
    mutation AddItemToProject($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: { projectId: $projectId, contentId: $contentId }) {
        item { id }
      }
    }
  `, { projectId, contentId });
  return result.addProjectV2ItemById.item.id;
}

async function updateSingleSelectField(github, projectId, itemId, fieldId, optionId) {
  await github.graphql(`
    mutation UpdateField($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
      updateProjectV2ItemFieldValue(input: {
        projectId: $projectId, itemId: $itemId, fieldId: $fieldId,
        value: { singleSelectOptionId: $optionId }
      }) { projectV2Item { id } }
    }
  `, { projectId, itemId, fieldId, optionId });
}

async function fetchProjectFields(github, projectId) {
  // NOTE: fields(first: 50) caps results to first 50 fields on the board.
  const result = await github.graphql(`
    query FetchFields($projectId: ID!) {
      node(id: $projectId) {
        ... on ProjectV2 {
          fields(first: 50) {
            nodes {
              ... on ProjectV2SingleSelectField {
                id name options { id name }
              }
            }
          }
        }
      }
    }
  `, { projectId });
  const fieldMap = {};
  for (const node of result.node.fields.nodes) {
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
