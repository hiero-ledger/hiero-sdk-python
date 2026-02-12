# 02: How Workflows Are Structured (Orchestration + Logic)

Building on the basics from [01-what-are-workflows.md](./01-what-are-workflows.md), this document explains **exactly how** we structure workflows in the Hiero Python SDK repository.

We use a very deliberate pattern called **Orchestration vs. Logic separation**.  
This makes it much easier for you (and future contributors) to **create**, **tweak**, **understand**, and **maintain** automations.

## The Simple Flow

1. Something happens on GitHub  
   (someone comments `/assign`, a PR is opened, code is pushed…)

2. ↓

3. The **workflow (.yml)** wakes up and quickly decides:  
   “Should this run right now?”  
   (based on event type, branch, labels, etc.)

4. ↓

5. If yes → it calls the matching **script (.js)**

6. ↓

7. The **script** does all the real work  
   (reads details, thinks, decides, talks to GitHub, writes comments…)

8. ↓

9. Results show up in GitHub  
   (comment posted, label added, check passed/failed, log messages…)

## Two Folders – Two Very Different Jobs

| Folder                        | File type     | Role              | Contains mostly…                                 | Thinking allowed? |
|-------------------------------|---------------|-------------------|--------------------------------------------------|-------------------|
| `.github/workflows/`          | `*.yml`       | **Orchestration** | When to run, permissions, setup, calling script  | Almost none       |
| `.github/scripts/`            | `*.js` (main) | **Business Logic**| Decisions, API calls, calculations, comments     | All of it         |

**Golden rule used by the maintainers:**

> If it involves **thinking**, **deciding**, **checking conditions**, **calling APIs**, **handling errors**, or **writing messages to users** → put it in a **script**.<br>
> If it is only about **starting the process**, **setting security**, or **connecting things** → put it in the **workflow YAML**.

## What Each Layer Is Responsible For

### Workflows (.github/workflows/*.yml) – Orchestration

Responsible for:

- Defining **triggers** (`on: pull_request`, `on: issue_comment`, etc.)
- Setting **permissions** (`permissions: { issues: write }`)
- Selecting **runners** (`runs-on: ubuntu-latest`)
- Controlling **concurrency** (prevent duplicate runs)
- Wiring **inputs**, **environment variables**, **secrets**
- Calling the script (usually via `actions/github-script`)

Should contain **almost zero decision-making logic**.  
Complex `if:` conditions, string parsing, API calls, etc. do **not** belong here.

### Scripts (.github/scripts/*.js) – Business Logic

Responsible for:

- Interpreting the **event payload** (`context.payload`)
- Making **decisions** (“Is this a valid /assign?”, “Does the issue have the right label?”)
- Calling **GitHub APIs** (`github.rest.issues.addLabels`, `createComment`, …)
- Computing **results**
- Handling **errors** (`try/catch`, `core.setFailed`)
- Producing **logs** (`core.info`, `core.warning`)
- Generating **user-facing comments** (helpful messages, emojis, instructions)

**If it involves thinking → it belongs in the script.**

## Naming Convention (Very Important!)

We deliberately name workflows and their scripts **very similarly** so you can instantly see which files belong together:

Examples from the repository:

- `.github/workflows/bot-gfi-assign-on-comment.yml`  
  → `.github/scripts/bot-gfi-assign-on-comment.js`

This makes scanning `.github/` much faster when you want to understand or fix something.

## Best Practices Summary

- **Workflows** should have a **good, descriptive title**  
  (the `name:` field – it appears in the Actions tab and in PR checks)  
  Good: `Beginner Issues – Auto-assign when /assign is commented`  
  Bad: `assign`

- **Scripts** should be **well documented**:
  - Start with a comment block explaining **purpose**
  - Add inline comments for any non-obvious logic
  - Example:
    ```js
    // Purpose: Assigns a good-first-issue only if it's still free and correctly labeled
    // Allowed only via /assign command in issue comments
    ```
    