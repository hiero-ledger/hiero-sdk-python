## Handling Conflicts

## Table of Contents
- [Handling Conflicts](#handling-conflicts)
  - [1. See which files are conflicted](#1-see-which-files-are-conflicted)
  - [2. Resolve conflicts manually](#2-resolve-conflicts-manually)
  - [3. Resolving conflicts in VS Code (recommended):](#3-resolving-conflicts-in-vs-code-recommended)
    - [Steps to resolve:](#steps-to-resolve)
- [After fixing conflicts:](#after-fixing-conflicts)
  - [4. Stage the resolved files](#4-stage-the-resolved-files)
  - [5.Continue the rebase](#5continue-the-rebase)
  - [6. After Rebase is Completed](#6-after-rebase-is-completed)
- [Common issues](#common-issues)
- [If you need to stop](#if-you-need-to-stop)
- [What NOT to do](#what-not-to-do)
- [Recovery Tips:](#recovery-tips)
  - [If you are completely stuck](#if-you-are-completely-stuck)





Conflicts are common if main has updates to the files you are working on. In which case, you'll have to run a rebase.

If you are warned of a conflict:

- In VS Code: open the conflicted files and use the built-in conflict resolution.

### 1. See which files are conflicted
```bash
git status
```

### 2. Resolve conflicts manually
You will see sections like:

```text
<<<<<<< HEAD
code from main
======= 
your branch’s code
>>>>>>> mybranch     
```

1. Decide what the final code should be.

2. Sometimes keep main, sometimes your branch, sometimes both.

### 3. Resolving conflicts in VS Code (recommended):
VS Code provides an easier 3-pane interface for resolving conflicts:

-> Incoming Change → code from main (left/top)

-> Current Change → code from your branch (right/top)

-> Result → the lower/third pane, where you create the final merged file

#### Steps to resolve:

1. Open the conflicted file in VS Code.

2. Look at both the Incoming Change and Current Change panels.

3. In the Result (lower pane), edit the file so it contains the correct final version.

-> Sometimes keep Incoming (main)

-> Sometimes keep Current (your branch)

-> Often, combine both parts.

4. Save the file. If the conflict is resolved correctly, VS Code will mark it as fixed.

5. If there are more conflicts, VS Code will automatically move you to the next one. Repeat until no conflicts remain.

⚠️ Do NOT just click “Accept All Incoming” or “Accept All Current” — that usually deletes important code.

## After fixing conflicts:

### 4. Stage the resolved files
```bash
git add .
```

### 5.Continue the rebase
```bash
git rebase --continue
```
Repeat until all conflicts are resolved.

### 6. After Rebase is Completed

Once the rebase finishes successfully:

- Your commits may look “different” (new commit hashes) — this is expected, since rebase rewrites history.
- If you already have an open Pull Request, you will need to update it with a **force push**, before pushing, double-check that your commits are both DCO signed and GPG verified:
```bash
git log --show-signature
```
then:
```bash
git push --force
```

**Tip**: To be safe, create a backup branch before force pushing:
```bash
git checkout -b mybranch-backup
```


## Common issues
Message: “No changes – did you forget to use git add?”
→ This means you resolved the conflicts but forgot to stage them. Run git add . and try again.

Message: “Are you sure you want to continue with conflicts?”
→ This means some conflicts are still unresolved or you did not save the files properly.
Double-check your files in VS Code, make sure they are saved, and resolve any remaining conflict markers (<<<<<<<, =======, >>>>>>>).


## If you need to stop
```bash
git rebase --abort
```

**Tip**: At each conflict: resolve → save → stage → continue. Repeat until all conflicts are gone.

# What NOT to do
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

2. Reset your branch to match upstream/main:
``` bash
git checkout main
git reset --hard upstream/main
git checkout mybranch
git rebase upstream/main -S
```

⚠️ Use git stash only if you really want to save some local changes that aren’t yet committed. In most cases, if the rebase is failing, it’s safer to abort or reset rather than reapplying a stash of broken work.


- To check commit signatures (verified status):
```bash
git log --pretty="%h %G? %aN %s"
```
-> G = good signature (verified)
-> B = bad signature
-> U = unsigned commit
-> N = no signature

- To check for "Signed-off-by" lines:
This shows commits along with their sign-off lines, helping you verify compliance with DCO (Developer Certificate of Origin).
```bash
git log --pretty="%h %s%n%b" | grep -B1 -A0 "Signed-off-by:"
```
