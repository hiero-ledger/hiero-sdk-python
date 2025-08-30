# Rebasing (Hiero Python SDK)

If you have forked the Hiero Python SDK, created your own branch, and now need to sync it with the latest changes from main in the original repository, follow these steps.

## One-Time Setup

Only do this once per repository clone.

### Add the original repo as a remote called "upstream"
```bash
git remote add upstream https://github.com/hiero-ledger/hiero-sdk-python.git
```

## Update Your Main

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
```bash
git rebase main -S
```

## Handling Conflicts

Conflicts are common if main has updates to the files you are working on. In which case, you'll have to run a rebase.

If you are warned of a conflict:

- In VS Code: open the conflicted files and use the built-in conflict resolution.

After fixing conflicts:

Stage the files:
```bash
git add .
```
then continue rebasing: 
```bash
git rebase --continue
```
At each conflict instance, you'll have to repeat: fix the conflict, stage the files and continue rebasing.

**Tip**: Always sync your branch before opening or updating a Pull Request to reduce review friction and avoid merge conflicts.