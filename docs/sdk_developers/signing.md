# ✅ Commit Signing Guidelines (DCO + GPG)

To contribute to this repository, **both DCO sign-off and GPG signature verification** are required for your commits to be merged successfully.

This guide walks you through how to correctly configure and sign your commits, and how to ensure **all commits are properly signed**.

---

## 🛡️ Why Commit Signing?

* **DCO (`Signed-off-by`)** ensures you agree to the developer certificate of origin.
* **GPG Signature** proves the commit was authored by a trusted and verified identity.

---

## ✍️ Step-by-Step Setup

### 1. Generate a GPG Key

If you don’t already have a GPG key:

```bash
gpg --full-generate-key
```

Choose:

* Kind: RSA and RSA
* Key size: 4096
* Expiration: 0 (or choose as per your need)
* Name, Email: Must match your GitHub email
* Passphrase: Set a strong passphrase

To list your keys:

```bash
gpg --list-secret-keys --keyid-format LONG
```

Copy the key ID (looks like `34AA6DBC`).

---

### 2. Add Your GPG Key to GitHub

Export your GPG public key:

```bash
gpg --armor --export YOUR_KEY_ID
```

Paste the output into GitHub:

* [Add GPG key on Github](https://github.com/settings/gpg/new)

---

### 3. Configure Git to Use Your GPG Key

```bash
git config --global user.signingkey YOUR_KEY_ID
git config --global commit.gpgsign true
```

---

## ✨ Make Signed Commits

**All commits must be signed using both DCO and GPG.**

```bash
git commit -S -s -m "chore: your commit message"
```

* `-S` = GPG sign
* `-s` = DCO sign-off

> ⚠️ Ensure **every commit** in your branch follows this rule.

---

## 🛠️ Fixing Unsigned Commits

If you accidentally forgot to sign commits, there are **two ways to fix them**:

### 1. Soft Reverting Commits (Recommended for New Contributors)

Soft revert the impacted commits while keeping changes locally:

```bash
git reset --soft HEAD~n
```

* `HEADn` = number of commits to go back
* Example: To fix the last 3 commits: `git reset --soft HEAD`

Then, recommit each commit with proper signing:

```bash
git commit -S -s -m "chore: your commit message"
```

Repeat for each impacted commit.

---

### 2. Retroactively Signing Commits

Alternatively, you can **amend commits retroactively**:

```bash
git commit --amend -S -s
git rebase -i HEAD~n  # For multiple commits
git push --force-with-lease
```

> **Note:** `--force-with-lease` safely updates the remote branch without overwriting others’ changes.

---

## ✅ Verify Signed Status of Commits

To check that your commits are signed correctly:

```bash
git log --show-signature
```

* Ensure each commit shows both **GPG verified** and **DCO signed-off**.
* For a quick check of recent commits:

```bash
git log -n 5 --pretty=format:'%h %an %G? %s'
```

* `G?` column shows the signature status (`G` = good, `B` = bad, `U` = unsigned)

---

## ✅ Final Checklist

* [ ] All commits signed with `-S`
* [ ] DCO added with `-s`
* [ ] GPG key added to GitHub
* [ ] Verified badge appears in PR

---

### Still Need Help?

* Refer to [GitHub’s GPG Docs](https://docs.github.com/en/authentication/managing-commit-signature-verification)
* Ask maintainers on the **Hiero Discord** if stuck
