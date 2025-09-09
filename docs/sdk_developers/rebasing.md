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
## Check Commit Signatures Before Rebasing

Before starting a rebase, make sure your commits are correctly signed. Unsigned commits may cause CI checks to fail after you push your branch.

#### 1. Verify existing commits

Run one of the following commands:

-> To check DCO (Developer Certificate of Origin) sign-off:
```bash
git log --pretty=format:"%h %s %b" | grep "Signed-off-by"
```

✅ Each commit should have a Signed-off-by: Your Name <email> line.

-> To check GPG-signed commits:
```bash
git log --show-signature
```

✅ Look for gpg: Good signature in the output.

-> Quick check for both:
```bash
git log --pretty=format:"%h %s %G?"
```

-> Legend:

G = Good (valid signature)
B = Bad (invalid signature)
U = Unknown (not signed)

#### 2.Project Requirement:
This project requires both DCO and GPG signed commits.

If you don’t have GPG keys set up, use -s for DCO sign-off.

If you do have GPG keys configured, prefer -S for extra verification.

**Tip**: Always use this to be safe:
```bash
git commit -s -S -m "Your-commit-message"
```

### 2. Rebase your branch on top of the updated main
# Rebase = cleaner history, your commits appear on top of main.

```bash
git rebase main -S
```

Note: The -S ensures your commits are signed.

## Handling Conflicts:
If conflicts occur during rebase, See [merge_conflicts.md](merge_conflicts.md) for detailed guidance.


**Tip**: Always sync your branch before opening or updating a Pull Request to reduce review friction and avoid merge conflicts.