const COMMENT_MARKER = "<!-- pr-draft-explainer -->";

module.exports = async ({ github, context, core }) => {
  const pr = context.payload.pull_request;
  const { owner, repo } = context.repo;

  if (!pr) {
    core.info("No pull request found in payload. Exiting.");
    return;
  }

  const prNumber = pr.number;
  const authorLogin = pr.user && pr.user.login ? pr.user.login : null;
  const greetingTarget = authorLogin ? `@${authorLogin}` : "there";

  core.info(
    `PR #${prNumber} was converted to draft. Checking if explanation is needed.`,
  );

  let comments = [];
  try {
    comments = await github.paginate(github.rest.issues.listComments, {
      owner,
      repo,
      issue_number: prNumber,
      per_page: 100,
    });
  } catch (error) {
    core.info(
      `Failed to list comments for PR #${prNumber}: ${error.message}. Skipping comment to avoid duplicates.`,
    );
    return;
  }

  const alreadyExplained = comments.some((comment) =>
    comment.body ? comment.body.includes(COMMENT_MARKER) : false,
  );

  if (alreadyExplained) {
    core.info("Draft explanation comment already exists. Skipping.");
    return;
  }

  try {
    const reviews = await github.rest.pulls.listReviews({
      owner,
      repo,
      pull_number: prNumber,
    });

    const hasChangeRequest = reviews.data.some(
      (review) => review.state === "CHANGES_REQUESTED",
    );

    if (!hasChangeRequest) {
      core.info("No change-request review found. Skipping explanation comment.");
      return;
    }
  } catch (error) {
    core.info(
      `Review lookup failed (${error.message}). Posting explanation anyway.`,
    );
  }

  const message = `${COMMENT_MARKER}
Hi ${greetingTarget}!

We suggested a few updates and moved this PR to **draft** while you apply the feedback. This keeps it out of the review queue until it is ready again.

### What happens next?
- Make the requested changes.
- When you are ready, click **"Ready for review"** at the top of the PR or comment \`/ready\`.

Thanks again for your contribution!`;

  await github.rest.issues.createComment({
    owner,
    repo,
    issue_number: prNumber,
    body: message,
  });

  core.info(`Posted draft explanation comment on PR #${prNumber}.`);
};
