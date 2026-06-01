function isBotAuthor(pr) {
  const login = pr?.user?.login || '';
  return pr?.user?.type === 'Bot' || login.endsWith('[bot]');
}

function isDraft(pr) {
  return pr?.draft === true;
}

async function convertToDraft(github, { owner, repo, pullNumber }) {
  await github.rest.pulls.update({
    owner,
    repo,
    pull_number: pullNumber,
    draft: true,
  });
}

module.exports = {
  convertToDraft,
  isBotAuthor,
  isDraft,
};
