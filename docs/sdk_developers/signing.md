# ✅ Commit Signing Guidelines (DCO + GPG)

To contribute to this repository, **both DCO sign-off and GPG signature verification** are required for your commits to be merged successfully.

This guide walks you through how to correctly configure and sign your commits.

---

## 🛡️ Why Commit Signing?

- **DCO (`Signed-off-by`)** ensures you agree to the developer certificate of origin.
- **GPG Signature** proves the commit was authored by a trusted and verified identity.

---

## ✍️ Step-by-Step Setup

### 1. Generate a GPG Key

If you don’t already have a GPG key:

```bash
gpg --full-generate-key
```

Choose:

Kind: RSA and RSA

Key size: 4096

Expiration: 0 (or choose as per your need)

Name, Email: Must match your GitHub email

Passphrase: Set a strong passphrase 

To list your keys:

```bash
gpg --list-secret-keys --keyid-format LONG 
```
Copy the key ID (it looks like 34AA6DBC)

### 2. Add Your GPG Key to GitHub

Export your GPG public key:

```bash
gpg --armor --export YOUR_KEY_ID
```
Paste the output into GitHub here:


- [Add GPG key on Github ](https://github.com/settings/gpg/new)

### 3. Tell Git to Use Your GPG Key

```bash
git config --global user.signingkey YOUR_KEY_ID
git config --global commit.gpgsign true
```

### 4. Make a Signed Commit

Use both DCO sign-off and GPG signing:

```bash
git commit -S -s -m "chore: your commit message"
```

-S = GPG sign
-s = DCO sign-off

### Fixing an Unsigned Commit

If you forgot to sign or DCO a commit:

```bash
git commit --amend -S -s
git push --force-with-lease
```
## Rebasing and Signing

Rebase operations will be required when your branch is behind the upstream main. See [rebasing.md](./rebasing.md) for instructions on how to keep your main branch up to date and how to rebase.

When rebasing, you must use this command to ensure your commits remain verified:

```bash
git rebase main

## ✅ Final Checklist

- [ ] Signed your commit with `-S`
- [ ] Added DCO with `-s`
- [ ] GPG key is added to GitHub
- [ ] Verified badge appears in PR


### Still Need Help?

If you run into issues:

- Refer to [GitHub’s GPG Docs](https://docs.github.com/en/authentication/managing-commit-signature-verification)
