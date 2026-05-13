const {
  convertToDraft,
  getPresentManagedLabels,
  isBotAuthor,
  isDraft,
  removeManagedLabels,
} = require('./helpers');

module.exports = async function revisionGuard({ github, context, core }) {
  const reviewState = context.payload.review?.state;
  const pr = context.payload.pull_request;

  if (!pr || reviewState !== 'changes_requested') {
    return;
  }

  if (isBotAuthor(pr)) {
    core?.info?.(`Skipping PR #${pr.number} because it is bot-authored.`);
    return;
  }

  if (isDraft(pr)) {
    core?.info?.(`Skipping PR #${pr.number} because it is already a draft.`);
    return;
  }

  await convertToDraft(github, pr.node_id);
  core?.info?.(`Converted PR #${pr.number} to draft.`);

  const labelsToRemove = getPresentManagedLabels(pr.labels);
  if (labelsToRemove.length === 0) {
    core?.info?.(`No managed labels to remove for PR #${pr.number}.`);
    return;
  }

  await removeManagedLabels(github, {
    owner: context.repo.owner,
    repo: context.repo.repo,
    issueNumber: pr.number,
    labels: labelsToRemove,
  });
  core?.info?.(
    `Removed managed labels from PR #${pr.number}: ${labelsToRemove.join(', ')}.`
  );
};
