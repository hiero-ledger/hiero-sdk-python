const { parseManagedLabels } = require('./constants');

function getManagedLabels() {
  return parseManagedLabels(process.env.REVISION_GUARD_MANAGED_LABELS);
}

function getPresentManagedLabels(prLabels, managedLabels = getManagedLabels()) {
  const currentLabels = Array.isArray(prLabels)
    ? prLabels
        .map(label => typeof label === 'string' ? label : label?.name)
        .filter(Boolean)
    : [];

  return managedLabels.filter(label => currentLabels.includes(label));
}

async function removeManagedLabels(github, { owner, repo, issueNumber, labels }) {
  for (const name of labels) {
    try {
      await github.rest.issues.removeLabel({
        owner,
        repo,
        issue_number: issueNumber,
        name,
      });
    } catch (error) {
      if (error?.status !== 404) {
        throw error;
      }
    }
  }
}

module.exports = {
  getManagedLabels,
  getPresentManagedLabels,
  removeManagedLabels,
};
