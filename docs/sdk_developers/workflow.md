# Workflow for Python SDK Development

Welcome! 
This guide will explain to you the best-practice workflow when developing the Python SDK.
You are strongly recommended to follow this workflow in order to create merge-ready pull requests.

## Table of Contents
- [Workflow 1: Updated Main](#workflow-1-updated-main)
- [Workflow 2: Branch From Main](#workflow-2-branch-from-main)
- [Workflow 3: DCO and GPG Sign Commits](#workflow-3-dco-and-gpg-sign-commits)
- [Workflow 4: Add Examples](#workflow-4-add-examples)
- [Workflow 5: Add Unit and Integration Tests](#workflow-5-add-unit-and-integration-tests)
- [Workflow 6: Update Changelog](#workflow-6-update-changelog)
- [Workflow 7: Submit Your Pull Request](#workflow-7-submit-your-pull-request)

### Workflow 1: Updated Main
The Python SDK updates regularly and you must keep your repository in sync when developing and creating pull requests. 

If your main is not in sync:
- ❗ Pull requests are unlikely to be approved
- ❗ You'll need to resolve conflicts (which is difficult)
- ❗ You'll have to update it anyway

To keep your project updated, a pre-requisite (to do once) is to make sure your project is tied to ours:
```bash
git remote -v
```

Should output:
```bash
origin https://github.com/your_github_name/hiero_sdk_python.git (fetch)
origin https://github.com/your_github_name/hiero_sdk_python.git (push)
upstream https://github.com/hiero-ledger/hiero-sdk-python.git (fetch)
upstream https://github.com/hiero-ledger/hiero-sdk-python.git (push)
```

If not:
```bash
git remote add upstream https://github.com/hiero-ledger/hiero-sdk-python.git
```

Now you can pull upstream changes to your main:
```bash
git checkout main
git fetch upstream
git pull upstream main
```
You can also update your repository via GitHub online - travel to the repository and click "Sync fork" near the top right. Then pull changes on github desktop.

Once your main is updated, update your working branch by doing:
```bash
git checkout branch-name
git rebase main -S
```
**IMPORTANT** do NOT "git merge main" or "git rebase main". This usually corrupts your work or removes signing and is difficult to resolve, for example, you'll need to resign everything afterwards.


### Workflow 2: Branch From Main

Always work from a branch of your main.

Every single issue = one new branch from main.

Working on main will eventually lead to:
- ❗ Sync issues
- ❗ Sign issues
- ❗ Corruption issues
- ❗ PR's that cannot be approved

Do not work from main, instead, work on a branch.

First, create a branch:
```bash
git checkout -b 123-readme-link-fix
```

Name your branch appropriately pre-fixed by the issue ID you are working on.

Correct names:
- ✅ `123-readme-link-fix`
- ✅ `456-add-examples`

Incorrect names:
- ❌ `readme-fix`


### Workflow 3: DCO and GPG Sign Commits
**Each** commit must be DCO and GPG key signed:

```bash
git commit -S -s -m "chore: your commit message"
```

You'll need a GPG key and a tie to github explained at [signing.md](signing.md)

Avoid commiting the issue solution all-in-one.
✅ Commit key portions of work making it easier to revert sections if needed

For example:
```bash
git commit -S -s -m "fix: token id to string bug"
```

```bash
git commit -S -s -m "chore: changelog entry token id to string bug"
```

Do not:
- ❌ Use commit-assist tools
- ❌ git merge main or github desktop merge
- ❌ git rebase main or github desktop rebase

Safe:
- ✅ git rebase main -S 

### Workflow 4: Add Examples
When you add a feature to /src, we recommend adding an example. Update:
- [ ] /examples with the new example file(s). 
- [ ] docs/sdk_users/running_examples with a high level pythonic or method chaining example
- [ ] scripts/run_examples.py, importing your example and 'EXAMPLES_TO_RUN'. This will add your example to our workflow testing examples run.


### Workflow 5: Add Unit and Integration Tests
When you add a feature to /src, we recommend adding unit and integration tests.
Read about creating tests here: [testing guide](testing.md)



### Workflow 6: Update Changelog
Under the existing [UNRELEASED] section, add a one-sentence description of your addition, change or fix to [CHANGELOG.md](/./CHANGELOG.md)

See [Changelog Entry Guide](/docs/sdk_developers/changelog_entry.md)

- ✅ **IMPORTANT** keep your main and branch regularly else your changelog will be out of date and it will be more difficult to resolve.

### Workflow 7: Submit Your Pull Request
First, ensure your commits in your branch are published and meet [checklist](checklist.md).

Then:
1. Visit [Pull Requests](https://github.com/hiero-ledger/hiero-sdk-python/pulls)
2. Click the orange banner at the top: "Compare & pull request"
3. Briefly fill out the pull request template.
**IMPORTANT** under "##Fixes" link the issue solved.

