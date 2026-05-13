function isBotAuthor(pr) {
  const login = pr?.user?.login || '';
  return pr?.user?.type === 'Bot' || login.endsWith('[bot]');
}

function isDraft(pr) {
  return pr?.draft === true;
}

async function convertToDraft(github, pullRequestId) {
  await github.graphql(
    `
      mutation($pullRequestId: ID!) {
        convertPullRequestToDraft(input: { pullRequestId: $pullRequestId }) {
          pullRequest {
            isDraft
          }
        }
      }
    `,
    { pullRequestId }
  );
}

module.exports = {
  convertToDraft,
  isBotAuthor,
  isDraft,
};
