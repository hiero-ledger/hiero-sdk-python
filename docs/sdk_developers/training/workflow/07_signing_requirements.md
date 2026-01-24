## DCO and GPG Verified Commit Signing Requirements for the Python SDK
At the Python SDK we require **each** commit in a pull request to be:
- DCO signed (this is achieved with a -s flag)
- GPG key signed (this is achieved with a -S flag and a GPG key set up and tied to GitHub)

To pass our workflows and be merge-ready.

Therefore, use Terminal or a Command Line Interface when creating each commit and ensure the message is:
```bash
git commit -S -s -m "prefix: your commit message"
```
For example:
```bash
git commit -S -s -m "chore: changelog entry for TokenCreateTransaction"
```

**WARNING**: using the default commit button on GitHub desktop or VS Studio will result in un-signed commits.

**WARNING** any merge or rebase operations will cause a loss of signing status unless you preserve signing: `git rebase main -S`

Read more about signing and how to set up a GPG key at:
[Signing Guide](../../signing.md)
