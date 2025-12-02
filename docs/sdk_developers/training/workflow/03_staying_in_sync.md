### Syncing Your Repo with the Upstream Python SDK

Development at the Python SDK can be fast meaning new changes are added frequently.

It is important to frequently pull new changes at the Python SDK to your local repository to ensure you are working on the most updated code and avoid merge_conflicts.

To do this:

1. Link the Upstream Python SDK Remote with yours
Link your fork to the upstream original Python SDK repository so you can easily bring in new updates from main.

```bash
git remote add upstream https://github.com/hiero-ledger/hiero-sdk-python.git
```

Then verify it is correctly set:
```bash
git remote -v
```

You should now see:
origin → your fork
upstream → the official Python SDK repo

2. Before starting work and during a pull request, always fetch new changes:
git checkout main
git fetch upstream
git pull upstream main

Then rebase on your working branch to apply the new changes:
git checkout mybranch
git rebase main -S