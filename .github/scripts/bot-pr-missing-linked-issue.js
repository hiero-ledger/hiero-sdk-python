const LINKBOT_MARKER = '<!-- LinkBot Missing Issue -->';

module.exports = async ({ github, context }) => {
  let prNumber;
  try {
    const isDryRun = process.env.DRY_RUN === 'true';
    prNumber = Number(process.env.PR_NUMBER) || context.payload.pull_request?.number;

    if (!prNumber) {
      throw new Error('PR number could not be determined');
    }

    console.log(`Processing PR #${prNumber} (Dry run: ${isDryRun})`);

    // For workflow_dispatch, we need to fetch PR details
    let prData;
    if (context.payload.pull_request) {
      prData = context.payload.pull_request;
    } else {
      // workflow_dispatch case - fetch PR data
      const prResponse = await github.rest.pulls.get({
        owner: context.repo.owner,
        repo: context.repo.repo,
        pull_number: prNumber,
      });
      prData = prResponse.data;
    }

    const authorType = prData.user?.type;
    const authorLogin = prData.user?.login;

    if (authorType === "Bot" || authorLogin?.endsWith('[bot]')) {
      console.log(`Skipping comment: PR created by bot (${authorLogin})`);
      return;
    }

    const body = prData.body || "";
    const regex = /\b(Fixes|Closes|Resolves)\s*:?\s*(#\d+)(\s*,\s*#\d+)*/i;

    const comments = await github.rest.issues.listComments({
      owner: context.repo.owner,
      repo: context.repo.repo,
      issue_number: prNumber,
    });

    const alreadyCommented = comments.data.some(comment =>
      comment.body?.includes(LINKBOT_MARKER)
    );

    if (alreadyCommented) {
      console.log('LinkBot already commented on this PR');
      return;
    }

    if (!regex.test(body)) {
      const safeAuthor = authorLogin ?? 'there';
      const commentBody = [`${LINKBOT_MARKER}` +
        `Hi @${safeAuthor}, this is **LinkBot** 👋`,
        ``,
        `Linking pull requests to issues helps us significantly with reviewing pull requests and keeping the repository healthy.`,
        ``,
        `🚨 **This pull request does not have an issue linked.**`,
        ``,
        `Please link an issue using the following format:`,
        `- Fixes #123`,
        ``,
        `📖 Guide:`,
      `[docs/sdk_developers/how_to_link_issues.md](https://github.com/${context.repo.owner}/${context.repo.repo}/blob/main/docs/sdk_developers/how_to_link_issues.md)`,
        ``,
        `If no issue exists yet, please create one:`,
      `[docs/sdk_developers/creating_issues.md](https://github.com/${context.repo.owner}/${context.repo.repo}/blob/main/docs/sdk_developers/creating_issues.md)`,
        ``,
        `Thanks!`
      ].join('\n');

      if (isDryRun) {
        console.log('DRY RUN: Would post the following comment:');
        console.log('---');
        console.log(commentBody);
        console.log('---');
      } else {
        await github.rest.issues.createComment({
          owner: context.repo.owner,
          repo: context.repo.repo,
          issue_number: prNumber,
          body: commentBody,
        });
        console.log('LinkBot comment posted successfully');
      }
    } else {
      console.log('PR has linked issue - no comment needed');
    }
  } catch (error) {
    console.error('Error processing PR:', error);
    console.error('PR number:', prNumber);
    console.error('Repository:', `${context.repo.owner}/${context.repo.repo}`);
    throw error;
  }
};