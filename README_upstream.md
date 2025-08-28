# Keeping Your Branch Up to Date with Main (Hiero Python SDK)

If you have forked the Hiero Python SDK, created your own branch, and now need to sync it with the latest changes from main in the original repository, follow these steps.

## One-Time Setup

Only do this once per repository clone.

### Add the original repo as a remote called "upstream"
```bash
git remote add upstream https://github.com/hiero-ledger/hiero-sdk-python.git
```

## Quick Cheatsheet
- Sync main:  
  ```bash
  git checkout main
  git fetch upstream
  git pull upstream main
```

- Rebase branch:
  ```bash
  git checkout mybranch
  git rebase main -S
```


## Update Your Main

Your local main should always be an exact copy of the original repo’s main.
Never commit directly to it. Never open PRs from it.

Update your main easily with the latest python sdk main by visiting your repository https://github.com/your_name/hiero_sdk_python and clicking the sync fork button which is a few lines from the top near the right.

Alternatively run these commands every time you want to update your branch with the latest main.

### 1. Switch to your local main branch
```bash
git checkout main
```

### 2. Get the latest main branch from the original repo
```bash
git fetch upstream
```

### 3. Update local main to match upstream/main
```bash
git pull upstream main
```

## Update Your Branch

Run these commands to update your branch with the content from main.

It is necessary to run these commands if main updates with changes that impact what you are working on. 

### 1. Switch back to your branch
```bash
git checkout mybranch
```

### 2. Rebase your branch on top of the updated main
# Rebase = cleaner history, your commits appear on top of main.
The -S ensures your commits are signed.

```bash
git rebase main -S
```

## Handling Conflicts

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

3. ⚠️ Do NOT just click “Accept All Incoming” or “Accept All Current” — that usually deletes important code.

## After fixing conflicts:

### 3. Stage the resolved files
```bash
git add .
```
**Note**: If you see "No changes - did you forget to use ‘git add’?", it means you must stage your fixes before running git rebase --continue.

### 4.Continue the rebase
```bash
git rebase --continue
```
Repeat until all conflicts are resolved.

## If you need to stop
```bash
git rebase --abort
```

# What NOT to do
1. ❌ Do not run git merge main
→ This creates messy merge commits. Always rebase instead.

2. ❌ Do not merge into your local main
→ Keep main as a clean mirror of upstream/main.

3. ❌ Do not open PRs from your fork’s main
→ Always create a feature branch for your changes.

At each conflict instance, you'll have to repeat: fix the conflict, stage the files and continue rebasing.

## Recovery Tips:

- Undo the last rebase commit (but keep changes staged):
```bash
git reset --soft HEAD~1
```

- Abort the rebase entirely(go back to branch state before rebase):
```bash
git rebase --abort
```

- If stuck, stash your work, resync main and reapply:
```bash
git stash
git rebase --abort
git checkout main
git reset --hard upstream/main
git checkout mybranch
git rebase upstream/main -S
git stash pop
```

- Check that commits are signed:
```bash
git log --show-signature
```


**Tip**: Always sync your branch before opening or updating a Pull Request to reduce review friction and avoid merge conflicts.