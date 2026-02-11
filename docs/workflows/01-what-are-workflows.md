# 01: What are Workflows?

Welcome to the Hiero Python SDK! To ensure a smooth, safe, and professional contribution experience, this repository relies heavily on **GitHub Workflows**. This guide explains the foundational concepts of repository automation and how it helps you as a contributor.

### What is a Workflow?
A workflow is an automated process that is **event-driven**. It stays inactive until a specific "Trigger" occurs. 

*   **The Trigger:** This is the **"When"** (e.g., someone comments `/assign` on an issue).
*   **The Logic:** This is the **"How"** (e.g., the system checks if you are eligible and then assigns you).

---

## The Anatomy of a Hiero Workflow
Every workflow in this repository follows a standardized design pattern to maintain security and consistency. 

#### 1. Job Title
Every workflow defines one or more **Jobs**. These are the top-level tasks (like `lint`, `test`, or `assign`). You can see these names in the "Actions" tab of the repository to track the progress of your contribution.

#### 2. Triggers (`on:`)
Workflows are defined by their triggers. Common triggers in this repo include:
*   `pull_request`: Runs when you open or update a PR.
*   `issue_comment`: Runs when you type a command in an issue.
*   `push`: Runs when code is merged into the main branch.

#### 3. Security Shield (`harden-runner`)
Security is our top priority. We use `step-security/harden-runner` in every workflow.
*   **Purpose:** It creates a "secure perimeter" around the temporary computer running the code. It ensures that the workflow only communicates with trusted endpoints (like GitHub) and prevents unauthorized data from leaving the environment.

#### 4. Workspace Setup (`checkout`)
GitHub starts every workflow on a clean, empty virtual machine. The `actions/checkout` step "downloads" a copy of the Hiero repository onto that machine so the automation can interact with our files.

---

## Why Workflows Call Scripts (Orchestration vs. Logic)
You will notice that our workflow files (YAML) often call external **scripts** located in [`.github/scripts/`](../../.github/scripts).

*   **YAML (The Orchestrator):** Handles the "When." It manages the triggers, the security steps, and the environment setup.
*   **Scripts (The Logic):** Handles the "How." We use JavaScript, Python, or Bash scripts for complex decision-making.

**Why the separation?** Scripts are easier to read, test, and debug. Complex tasks—such as checking if a contributor has completed a "Good First Issue" before assigning them a "Beginner" task—require the advanced logic that only a script can provide.

---

## Why We Rely on Automation
With over 30 workflows running in this repository, automation is the backbone of our "Support Infrastructure."

| Benefit | Explanation |
| :--- | :--- |
| **Better Developer Experience (DX)** | You get instant feedback. Our Linters find formatting errors in seconds, so you don't have to wait days for a human review. |
| **Safety** | Automation acts as a "Safety Net." Our test suite runs on every PR, ensuring that new changes don't accidentally break existing features. |
| **Scalability** | Automation allows the project to grow. Bots handle the "boring" tasks (like assigning issues or labeling PRs) so maintainers can focus on high-level code architecture. |

---

## Case Study: The Auto-Assignment Bot
A great example of these concepts in action is our **Beginner Assignment Bot**. 

1.  **The Trigger:** A contributor types `/assign` on an issue.
2.  **The Logic:** The workflow calls `bot-beginner-assign-on-comment.js`. This "brain" checks if the issue is already taken and verifies the contributor's history.
3.  **The Result:** If everything is valid, the bot assigns the user immediately. This provides a **seamless DX**—you can start working on an issue at 3 AM without waiting for a maintainer to wake up and manually assign you.

---

## Troubleshooting: Handling Failed Status Checks
If a workflow check fails on your Pull Request:
1.  **Don't Panic:** Failures are often simple formatting issues.
2.  **Click "Details":** This takes you to the logs.
3.  **Find the Error:** The bot will usually point to the exact line of code that needs fixing.
4.  **Fix and Push:** Look for the red text in the logs. The bot will usually point to the exact file and line number that needs fixing.
