# ✅ Commit Signing Guidelines (DCO + GPG)

To contribute to this repository, **both DCO sign-off and GPG signature verification** are required for your commits to be merged successfully.

This guide walks you through how to correctly configure and sign your commits.

---

## Table of Contents

- [Achieving Verified Commits](#-achieving-verified-commits)
- [Step-by-Step Setup](#%EF%B8%8F-step-by-step-setup)
  - [1. Generate a GPG Key](#1-generate-a-gpg-key)
  - [2. Add Your GPG Key to GitHub](#2-add-your-gpg-key-to-github)
  - [3. Tell Git to Use Your GPG Key](#3-tell-git-to-use-your-gpg-key)
  - [4. Make a Signed Commit](#4-make-a-signed-commit)
  - [Fixing an Unsigned Commit](#fixing-an-unsigned-commit)
- [Final Checklist](#-final-checklist)
- [Additional Resources](#-additional-resources)

---

## ✨ Achieving Verified Commits

### Why Is This Important?

To have your pull request (PR) merged into the Hiero Python SDK, **all commits MUST be verified**. This means your commits need to display a "Verified" badge on GitHub, which requires:

1. **DCO Sign-off (`-s` flag)** - Ensures you agree to the [Developer Certificate of Origin](https://developercertificate.org/)
2. **GPG Signature (`-S` flag)** - Proves the commit was authored by a verified and trusted identity
3. **GPG Key Connected to Your GitHub Account** - Your GPG public key must be added to your GitHub account

### ⚠️ CRITICAL: BOTH Flags Are Required

**Your commits MUST use BOTH `-s` and `-S` flags together:**

```bash
git commit -S -s -m "your commit message"
```

- `-S` = GPG sign the commit
- `-s` = Add DCO sign-off

**Without both flags, your commits will NOT appear as verified, and your PR cannot be merged.**

### What You'll Need

- A GPG key pair (we'll help you generate one)
- Your GPG key added to your GitHub account
- Git configured to use your GPG key
- Your email on GitHub must match your GPG key email

### Next Steps

Follow the [Step-by-Step Setup](#%EF%B8%8F-step-by-step-setup) section below to configure everything correctly.

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

## ✅ Final Checklist

- [ ] Signed your commit with `-S` (GPG signature)
- [ ] Added DCO with `-s` (Developer Certificate of Origin)
- [ ] Both flags used together: `git commit -S -s -m "message"`
- [ ] GPG key is added to your GitHub account
- [ ] Git is configured with your GPG key ID
- [ ] Your GitHub email matches your GPG key email
- [ ] Verified badge appears in your PR commits

## 📚 Additional Resources

Before submitting your PR, make sure to review these important guides:

- [CONTRIBUTING.md](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/CONTRIBUTING.md) - Complete contribution workflow guide
- [rebasing.md](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/sdk_developers/rebasing.md) - Guide to keeping your branch updated
- [merge_conflicts.md](https://github.com/hiero-ledger/hiero-sdk-python/blob/main/docs/sdk_developers/merge_conflicts.md) - How to resolve merge conflicts

### Still Need Help?

If you run into issues:

- Refer to [GitHub's GPG Docs](https://docs.github.com/en/authentication/managing-commit-signature-verification)
- Visit the [Hiero Python SDK Discord](https://discord.com/channels/905194001349627914/1336494517544681563) for community support
- Check the [Issues](https://github.com/hiero-ledger/hiero-sdk-python/issues) page for similar questions
