## Handling Conflicts

Merge conflicts are caused by working on out-dated versions of the codebase, or another developer merging a change involving similar parts of the codebase to you.

> ⚠️ **Avoid Merge Conflicts** by syncing your branch regularly [Sync Guide](rebasing.md)

## Table of Contents

- [Handling Conflicts](#handling-conflicts)
- [Resolving CHANGELOG.md Conflicts Using GitHub's Web Editor](#resolving-changelogmd-conflicts-using-githubs-web-editor)
- [Step-by-Step Guide to Resolve Merge Conflicts Locally](#step-by-step-guide-to-resolve-merge-conflicts-locally)
  - [1. See which files are conflicted](#1-see-which-files-are-conflicted)
  - [2. Understand what conflicts](#2-understand-what-conflicts)
  - [3. Decide what the final code should be](#3-decide-what-the-final-code-should-be)
  - [4. Resolve conflicts in VS Code (recommended)](#4-resolve-conflicts-in-vs-code-recommended)
    - [Steps to resolve in VS Code](#steps-to-resolve-in-vs-code)
      - [1. Open the conflicted file in VS Code](#1-open-the-conflicted-file-in-vs-code)
      - [2. Look at both the Incoming and Current changes](#2-look-at-both-the-incoming-change-left-and-current-change-right-panels)
      - [3. Edit the Result pane](#3-in-the-result-lower-pane-edit-the-file-so-it-contains-the-correct-final-version)
      - [4. Save the resolved file](#4-save-the-lower-pane-file-once-there-are-no-more-merge-conflicts-to-resolve-in-this-file)
      - [5. Stage the resolved files](#5-click-the-add-button-next-to-the-file-to-resolve-conflicts-or)
      - [6. Continue the rebase](#6-continue-the-rebase)
      - [7. Resolve remaining conflicts](#7-if-there-are-more-conflicts-in-other-files-vs-code-will-automatically-move-you-to-the-next-one-repeat-until-no-conflicts-remain)
      - [8. Push changes](#8-push-changes)
  - [Common issues](#common-issues)
  - [If you need to stop](#if-you-need-to-stop)
  - [What NOT to do](#what-not-to-do)
  - [When to Use This Method](#when-to-use-this-method)
  - [Steps](#steps)
- [Recovery Tips](#recovery-tips)
  - [If you are completely stuck](#if-you-are-completely-stuck)
- [Helpful Resources](#helpful-resources)


## Resolving CHANGELOG.md Conflicts Using GitHub's Web Editor

Changelog conflicts in CHANGELOG.md are very common in this repository because multiple pull requests frequently add new entries to the "Unreleased" section at the same time.

For these conflicts, there is a much simpler alternative to the full local rebase process: you can resolve them directly in your Pull Request on GitHub using the built-in web editor. No local setup or force push is required.

**Strong Recommendation**: Use the local VS Code rebase method (described below) to ensure full signing compliance. Use the web editor only if you are prepared to amend and re-sign the resolution commit locally afterward.

### When to Use This Method

- The conflict is only (or primarily) in `CHANGELOG.md`.
- You want to keep both sets of changes — this is almost always the correct choice for changelogs, as they are designed to accumulate all entries over time.

**Important**: The warnings above about not blindly accepting changes apply to code files. For CHANGELOG.md, "accepting both" is safe and recommended.

### Steps

1. In your PR, go to **Files changed** and scroll to the bottom. In the merge‑conflict banner, click **Resolve conflicts** to open the web editor.
2. In GitHub's web-based editor:
   - Conflicted sections are highlighted (usually in red/yellow).
   - You'll see **Incoming change** (from main) and **Current change** (from your branch) marked in red/highlighted areas.

3. **For a changelog conflict**:
   - Click **Accept both** (if the button is available) — this combines all the bullet-point entries perfectly.
   - If no "Accept both" button appears, manually remove the conflict markers (`<<<<<<< HEAD`, `=======`, `>>>>>>> your-branch`) and keep all entries from both sides.
   - Optionally, sort or group similar entries for neatness.

4. Once all conflicts are resolved, click **Mark as resolved** at the top of the editor.

5. You'll see a **Sign off and Commit** section:
   - Review your commit message
   - Click **Commit merge** (or **Commit directly to...** depending on your GitHub UI).

6. Your PR will update automatically, and the conflict will be resolved.

This method is especially beginner-friendly and avoids the more advanced local rebase steps.

For more details on GitHub's web-based editor, see: [The GitHub.dev web-based editor](https://docs.github.com/en/codespaces/the-githubdev-web-based-editor).
**Example**: See [PR `#1589`](https://github.com/hiero-ledger/hiero-sdk-python/pull/1589) for a real example of resolving a CHANGELOG.md conflict using this method.


## Step-by-Step Guide to Resolve Merge Conflicts Locally

### 1. See which files are conflicted
```bash
git checkout mybranch
git status
```

### 2. Understand what conflicts
You will see sections like:

```text
<<<<<<< HEAD
code from main
======= 
your branch’s code
>>>>>>> mybranch     
```

### 3. Decide what the final code should be

Have a vision of what you'd like the final code to look like, given what is currently on main and what you'd like to propose.

> ⚠️ **WARNING: Do not blindly accept both changes**. This often leads to problems.
> ⚠️ **WARNING: Do not blindly accept incoming**. This often leads to problems.
> ⚠️ **WARNING: Do not blindly accept existing**. This often leads to problems.

Merge conflicts require:

✅ Human interpretation

Sometimes you'll be:
- Accepting both incoming and current
- Accepting only incoming
- Accepting only current
- Accepting **parts** of both incoming and current

Generally, you want to keep all changes that were merged to main, but additionally, layer on your changes.


> ✅  **Resolving Conflicts Requires Human Interpretation**. Merge conflicts require thinking about what the final piece should be, should it include both changes? some of each? none of one? 

> ✅  **Resolving Conflicts Requires Human Edits**. Merge conflicts require manually editing the code.


### 4. Resolve conflicts in VS Code (recommended):
Once you understand you have a merge conflict and have a vision of the the final document, we recommend using VS code.


VS Code makes solving merge-conflicts more easier with a 3-pane interface for resolving conflicts:

-> Incoming Change → code from main (left/top)

-> Current Change → code from your branch (right/top)

-> Result → the lower/third pane, where you create the final merged file.

You want to accept or reject content from the top left and top right panes, and edit the final pane in the bottom so the final code submission reasonably resolves the issue while respecting the work of others.

#### Steps to resolve in VS Code:

##### 1. Open the conflicted file in VS Code.

##### 2. Look at both the Incoming Change (left) and Current Change (right) panels.

##### 3. In the Result (lower pane), edit the file so it contains the correct final version.

-> Sometimes keep Incoming (main)

-> Sometimes keep Current (your branch)

-> Often, combine both parts and edit the code manually.
If the conflict is resolved correctly, VS Code will mark it as fixed.

##### 4. Save the lower pane file once there are no more merge conflicts to resolve in this file.

##### 5. Click the add button next to the file to resolve conflicts or:
```bash
git add .
```

##### 6. Continue the rebase
```bash
git rebase --continue
```

##### 7. If there are more conflicts in other files, VS Code will automatically move you to the next one. Repeat until no conflicts remain.

⚠️ Do NOT just click “Accept All Incoming” or “Accept All Current” — that usually **deletes** or **corrupts** important code.

Once the rebase operation completes, your commits will be layered on top of main. It means your commit history will look “different” and you may even see changes to commits from other authors — this is expected, since rebase rewrites history. 

##### 8. Push changes
If you already have an open Pull Request, you will need to update it with a **force push**.

Before pushing, double-check that your commits are both DCO signed and GPG verified:

```bash
git log -n 5 --pretty=format:'%h %an %G? %s'
```
Replacing 5 with the number of commits backwards in history to check.

Ensure you see:
`G` = Good (valid signature)

then:
```bash
git push --force-with-lease
```

**Tip**: To be safe, create a backup branch before force pushing:
```bash
git checkout -b mybranch-backup
```

### Common issues
Message: “No changes – did you forget to use git add?”
→ This means you resolved the conflicts but forgot to stage them. Run git add . and try again.

Message: “Are you sure you want to continue with conflicts?”
→ This means some conflicts are still unresolved or you did not save the files properly.
Double-check your files in VS Code, make sure they are saved, and resolve any remaining conflict markers (<<<<<<<, =======, >>>>>>>).


### If you need to stop
```bash
git rebase --abort
```

**Tip**: At each conflict: resolve → save → stage → continue. Repeat until all conflicts are gone.

### What NOT to do
1. ❌ Do not run git merge main
→ This creates messy merge commits. Always rebase instead.

2. ❌ Do not merge into your local main
→ Keep main as a clean mirror of upstream/main.

3. ❌ Do not open PRs from your fork’s main
→ Always create a feature branch for your changes.

At each conflict instance, you'll have to repeat: fix the conflict, stage the files and continue rebasing.

## Recovery Tips:

- Undo the last rebase commit, but keep changes staged (while still in rebase):
If you are in the middle of a rebase and realize the last step went wrong, you can undo it while keeping changes staged:
```bash
git reset --soft HEAD~i
```

Note: The number after HEAD~ refers to how many commits you want to go back.

For example:
HEAD~1 → go back 1 commit
HEAD~3 → go back 3 commits
HEAD~5 → go back 5 commits

### If you are completely stuck
Sometimes a rebase can get too messy to fix conflict by conflict. In that case, it’s often easier to start fresh:

1. Abort the rebase to stop where you are:
```bash
git rebase --abort
```

2. Reset your fork's main to the upstream main and layer your commits on top of that:
``` bash
git checkout main
git reset --hard upstream/main
git push origin main --force-with-lease
git checkout mybranch
git rebase upstream/main -S
```

⚠️ Use git stash only if you really want to save some local changes that aren’t yet committed. In most cases, if the rebase is failing, it’s safer to abort or reset rather than reapplying a stash of broken work.

### Helpful Resources
- [Signing Guide](signing.md)
- [Rebasing Guide](rebasing.md)
- [Discord](../discord.md)