## Working on a Newly Assigned Issue in a Branch

Once you are assigned to an issue, you can get started working on it.

We require developers to work on a new branch for each new issue they are working on. This helps to avoid major sync issues and keep history clean.

Before you create a branch, remember to pull in all recent changes from main:
```bash
git checkout main
git fetch upstream
git pull upstream main
```

Then create a branch:
```bash
git checkout -b my-new-branch-name
```

Commit all your changes on this new branch, then publish your branch and submit a pull request.


