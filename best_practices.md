# Best Practices for Python SDK Development

Welcome! Glad you're here and want to contribute to the Hiero Python SDK.

Look, we've noticed a lot of new contributors run into the same problems, and most of them come down to working directly on the main branch. It causes headaches for everyone, so we wrote this guide to help you avoid those issues.

This isn't some formal rulebook - just practical advice from what we've seen work (and what definitely doesn't work).

## Table of Contents

- [Getting Started](#getting-started)
- [Setting Up Your Fork](#setting-up-your-fork)
- [Branch Management](#branch-management)
- [Development Workflow](#development-workflow)
- [Testing Your Changes](#testing-your-changes)
- [Committing Your Work](#committing-your-work)
- [Submitting Pull Requests](#submitting-pull-requests)

## Getting Started

Before you start coding:

**Read the docs.** Seriously, just skim through [CONTRIBUTING.md](../../CONTRIBUTING.md) and the [signing guide](./signing.md). It'll save you time later.

**Pick an issue.** Look for the `good first issue` label if this is your first time here.

**Claim it.** Comment on the issue saying you want to work on it. Wait for someone to assign it to you. This way two people don't end up doing the same work.

## Setting Up Your Fork

First time setting up? Here's what you need to do.

**Fork the repo:**

Go to https://github.com/hiero-ledger/hiero-sdk-python and hit that Fork button. This makes your own copy.

**Get it on your computer:**

```bash
git clone https://github.com/YOUR_USERNAME/hiero-sdk-python.git
cd hiero-sdk-python
```

**Connect it to the main project:**

```bash
git remote add upstream https://github.com/hiero-ledger/hiero-sdk-python.git
```

This `upstream` thing is important - it's how you stay synced with everyone else's work.

**Check it worked:**

```bash
git remote -v
```

Should show you four lines - two for `origin` (your fork) and two for `upstream` (the main project).

## Branch Management

This is where people mess up the most, so pay attention.

### Keep your main clean

Your main branch should just be a mirror of the project's main. Don't work on it. Don't commit to it. Just keep it updated.

**Before you start anything new:**

```bash
git checkout main
git fetch upstream
git pull upstream main
git push origin main
```

This grabs all the latest changes from the main project and updates your fork.

You can also do this through GitHub - go to your fork and click "Sync fork" if you see it. Then just pull those changes down.

**When your main gets messed up:**

Sometimes you accidentally commit to main. It happens. Here's how to fix it:

```bash
git checkout main
git reset --hard upstream/main
git push origin main --force
```

This nukes everything on your main and makes it match the project's main exactly. Just be sure you've saved any work you care about on another branch first.

### Use branches for everything

Every single issue = one new branch. Always.

Don't work on main. Just don't. Here's why:

When you work on main, you end up with:
- Changes from different issues all mixed together
- A fork that's impossible to sync
- PRs that are a nightmare to review
- Commits you can't undo
- Maintainers who are sad

Nobody wants sad maintainers.

## Development Workflow

Here's how to actually get work done:

### Starting fresh

```bash
# Make sure your main is current
git checkout main
git pull upstream main

# Make a new branch
git checkout -b issue-578-best-practices-doc
```

Name your branch something useful. Include the issue number. Future you will thank present you.

Good names:
- `issue-123-fix-balance-bug`
- `issue-456-add-examples`

Bad names:
- `fix`
- `updates`
- `new-branch`

### Doing the work

Code away! Just remember - only work on the one issue. If you notice something else that needs fixing, open a new issue for it and work on it separately.

### Testing as you go

Don't wait until the end to test. Run tests while you work:

```bash
pytest
```

Catches problems early when they're easier to fix.

### Keeping up to date

If you're working on something for a few days, the main branch might change. Update your branch:

```bash
git checkout main
git pull upstream main
git checkout issue-578-best-practices-doc
git merge main
```

If there are conflicts, Git will tell you. Fix them, then keep going.

## Testing Your Changes

Before you commit anything, make sure tests pass:

```bash
pytest
```

All of them need to pass. If you added something new, write tests for it. If you fixed a bug, maybe add a test so it doesn't come back.

If the project uses code formatting tools, run those too:

```bash
flake8
black --check .
```

## Committing Your Work

### Commit messages that make sense

Write commits like you're explaining to a coworker what you did.

Good:
- `fix: account balance rounds correctly now`
- `feat: added scheduled transaction support`
- `docs: updated the API examples`

Bad:
- `fixed stuff`
- `changes`
- `asdfgh`

### Signing commits (important!)

Every commit needs to be signed or your PR won't get merged. Use this format:

```bash
git commit -S -s -m "docs: wrote best practices guide"
```

The `-S` signs it with your GPG key. The `-s` adds a sign-off line. Both are required.

If you haven't set up GPG signing, go read [docs/sdk_developers/signing.md](./signing.md) first.

### Multiple commits are fine

You don't need to squash everything into one commit. Just sign each one:

```bash
git add some_file.py
git commit -S -s -m "feat: added the new function"

git add tests/
git commit -S -s -m "test: wrote tests for new function"
```

## Submitting Pull Requests

Almost done! Here's the final stretch.

### Push your branch

```bash
git push origin issue-578-best-practices-doc
```

### Don't forget the changelog

This trips people up all the time. Before you create your PR, you need to update `changelog.md`.

Find the `UNRELEASED` section and add what you did:

```markdown
## UNRELEASED

### Changed
- Wrote best practices guide for SDK developers
```

Pick the right category:
- `Added` - new stuff
- `Changed` - modified existing stuff
- `Fixed` - bug fixes
- `Removed` - deleted stuff

Then commit it:

```bash
git add changelog.md
git commit -S -s -m "chore: updated changelog"
git push origin issue-578-best-practices-doc
```

### Create the PR

1. Go to https://github.com/hiero-ledger/hiero-sdk-python/pulls
2. You'll see a yellow banner about your branch - click "Compare & pull request"
3. Fill out the template:
   - Say which issue this fixes (like "Closes #578")
   - Explain what you changed
   - Mention how you tested it

### What happens next

Someone will review your PR. They might:

**Approve it** - Nice! Your code gets merged.

**Ask for changes** - Normal. Just means they want you to tweak something.

**Ask questions** - They need clarification. Answer and discuss.

### If they ask for changes

Don't panic. Don't create a new PR. Just fix it on your existing branch:

```bash
# Make the changes they asked for
git add .
git commit -S -s -m "fix: updated based on review"
git push origin issue-578-best-practices-doc
```

Your PR updates automatically. Easy.

### Common screw-ups

**You pushed to main**

Oops. You'll need to:
1. Make a proper branch
2. Get your commits onto it
3. Reset your main
4. Push the branch

Ask for help if you get stuck here.

**You forgot to sign commits**

You'll need to fix them:

```bash
git rebase --exec 'git commit --amend --no-edit -S -s' -i HEAD~N
```

Where N is how many commits you need to fix. Then:

```bash
git push origin your-branch --force
```

**No changelog entry**

Can't merge without it. Add it and push another commit.

**Multiple issues in one PR**

This makes review really hard. Next time make separate branches for each issue.

---

## Quick Cheat Sheet

**Starting new work:**
```bash
git checkout main
git pull upstream main
git checkout -b issue-XXX-whatever
```

**Saving work:**
```bash
git add .
git commit -S -s -m "what you did"
git push origin issue-XXX-whatever
```

**Updating branch:**
```bash
git checkout main
git pull upstream main
git checkout issue-XXX-whatever
git merge main
```

---

Look, this might seem like a lot of steps at first. But once you do it a couple times, it becomes automatic. And it makes everything smoother - for you, for reviewers, for everyone.

The main thing is: keep your main clean, work on branches, sign your commits, update the changelog. Do those four things and you're golden.

Thanks for contributing!
