## Commit Message Requirements for the Python SDK
At the Python SDK we require commits to be descriptive and conventionally named in order to keep helpful records.

### Descriptive Commits
A descriptive commit is one that summarises in words what was just commited.

This is correct:

```bash
git commit -S -s -m "fix: fixed receipt status error catching in get_name"
```

This is incorrect:

```bash
git commit -S -s -m "looks like its mostly working now"
```

### Conventional Commits
Read about conventional commit messages here: [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/#summary)

This is correct:
```bash
git commit -S -s -m "chore: changelog entry to TokenCreateTransaction"
```

This is incorrect:
```bash
git commit -S -s -m "feat: changelog entry to TokenCreateTransaction"
```

This is incorrect:
```bash
git commit -S -s -m "changelog entry to TokenCreateTransaction"
```