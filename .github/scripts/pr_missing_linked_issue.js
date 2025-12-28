module.exports = async ({ github, context }) => {
  const body = context.payload.pull_request.body || "";
  const regex = /\bFixes\s*:?\s*(#\d+)(\s*,\s*#\d+)*/i;

  const comments = await github.rest.issues.listComments({
  owner: context.repo.owner,
  repo: context.repo.repo,
  issue_number: context.payload.pull_request.number,
  });

  const alreadyCommented = comments.data.some(comment =>
    comment.body.includes("this is LinkBot")
  );

  if (alreadyCommented) {
    return;
  }

  if (!regex.test(body)) {
    await github.rest.issues.createComment({
      owner: context.repo.owner,
      repo: context.repo.repo,
      issue_number: context.payload.pull_request.number,
      body: [
        `Hi @${context.payload.pull_request.user.login}, this is **LinkBot** 👋`,
        ``,
        `Linking pull requests to issues helps us significantly with reviewing pull requests and keeping the repository healthy.`,
        ``,
        `🚨 **This pull request does not have an issue linked.**`,
        ``,
        `Please link an issue using the following format:`,
        `- Fixes #123`,
        ``,
        `📖 Guide:`,
        `docs/sdk_developers/training/workflow/how_to_link_issues.md`,
        ``,
        `If no issue exists yet, please create one:`,
        `docs/sdk_developers/creating_issues.md`,
        ``,
        `Thanks!`
      ].join('\n')
    });
  }
};

