const {
  convertToDraft,
  getPresentManagedLabels,
  isBotAuthor,
  isDraft,
  removeManagedLabels,
} = require('./helpers');

module.exports = async function revisionGuard({ github, context, core }) {
  const payload = context?.payload;
  const repo = context?.repo;
  const reviewState = payload?.review?.state;
  const pr = payload?.pull_request;

  if (
    !payload ||
    !repo?.owner ||
    !repo?.repo ||
    !pr ||
    typeof pr.number !== 'number' ||
    reviewState !== 'changes_requested'
  ) {
    core?.info?.('Skipping revision guard due to missing or non-matching payload data.');
    return;
  }

  if (isBotAuthor(pr)) {
    core?.info?.(`Skipping PR #${pr.number} because it is bot-authored.`);
    return;
  }

  const labelsToRemove = getPresentManagedLabels(pr.labels);

  if (!isDraft(pr)) {
    if (process.env.REVIEWBOT_TOKEN && typeof pr.node_id === 'string') {
      try {
        await convertToDraft(github, {
          pullRequestId: pr.node_id,
        });
        core?.info?.(`Converted PR #${pr.number} to draft.`);
      } catch (error) {
        core?.error?.(
          `Failed to convert PR #${pr.number} to draft: ${error.message}. ` +
          'Continuing with managed label cleanup.'
        );
      }
    } else {
      core?.info?.(
        `Skipping draft conversion for PR #${pr.number}; REVIEWBOT_TOKEN is not configured.`
      );
    }
  } else {
    core?.info?.(`PR #${pr.number} is already a draft.`);
  }

  if (labelsToRemove.length === 0) {
    core?.info?.(`No managed labels to remove for PR #${pr.number}.`);
    return;
  }

  try {
    await removeManagedLabels(github, {
      owner: repo.owner,
      repo: repo.repo,
      issueNumber: pr.number,
      labels: labelsToRemove,
    });
    core?.info?.(
      `Removed managed labels from PR #${pr.number}: ${labelsToRemove.join(', ')}.`
    );
  } catch (error) {
    core?.error?.(
      `Failed to remove labels from PR #${pr.number}: ${error.message}. ` +
      `Labels to remove: ${labelsToRemove.join(', ')}.`
    );
    throw error;
  }
};
