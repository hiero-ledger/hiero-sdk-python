// ---------------------------------------------------------------------------
// Message Builders
// ---------------------------------------------------------------------------

function buildReminderMessage(commenter) {
  return `👋 Hi @${commenter}! If you'd like to work on this issue, please comment \`/assign\` to get assigned.`;
}

function getCurrentAssigneeMention(issue) {
  const login = issue?.assignees?.[0]?.login;
  return login ? `@${login}` : 'someone';
}

function unassignedIssuesUrl(owner, repo, label) {
  return `https://github.com/${owner}/${repo}/issues?q=${encodeURIComponent(
    `is:issue is:open label:"${label}" no:assignee`
  )}`;
}

function buildAlreadyAssignedMessage(commenter, issue, { owner, repo, label }) {
  return `👋 Hi @${commenter}, thanks for your interest! This issue is already assigned to ${getCurrentAssigneeMention(
    issue
  )}, but we'd love your help on another one. You can find more "${label}" issues [here](${unassignedIssuesUrl(
    owner,
    repo,
    label
  )}).`;
}

function buildGuardMessage(commenter, { owner, repo, prereqLabel, prereqDisplayName, requiredCount, currentDisplayName }) {
  const timesPhrase = requiredCount === 1 ? 'one' : requiredCount;
  const issuePhrase = requiredCount === 1 ? 'issue' : 'issues';
  return `👋 Hi @${commenter}! Thanks for your interest in contributing 💡\n\nBefore taking on a **${currentDisplayName}** issue, we ask contributors to complete at least ${timesPhrase} **${prereqDisplayName}** ${issuePhrase} first.\n\n👉 [Find one here](${unassignedIssuesUrl(
    owner,
    repo,
    prereqLabel
  )})\n\nOnce you've done that, come back — we'll be happy to assign this! 😊`;
}

function buildLimitMessage(commenter, { maxAllowed, spamLimited }) {
  return spamLimited
    ? `Hi @${commenter}, you are limited to **${maxAllowed} active issue${maxAllowed === 1 ? '' : 's'}** at a time. Please complete your current assignment before requesting another.`
    : `👋 Hi @${commenter}, you already have **${maxAllowed} open assignment${maxAllowed === 1 ? '' : 's'}**. Please finish one before requesting another.`;
}

function buildSpamBlockedMessage(commenter, { prereqDisplayName }) {
  return `Hi @${commenter}, your account is currently restricted to **${prereqDisplayName}** issues. Please complete one or contact a maintainer to have restrictions reviewed.`;
}

module.exports = {
  buildAlreadyAssignedMessage,
  buildGuardMessage,
  buildLimitMessage,
  buildReminderMessage,
  buildSpamBlockedMessage
};
