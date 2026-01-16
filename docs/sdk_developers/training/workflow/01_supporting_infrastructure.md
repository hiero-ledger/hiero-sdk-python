## Supporting Infrastructure When Developing for the Python SDK

For the best development experience and smoother support, we strongly recommend installing the following tools when developing for the Python SDK:

Recommended Tools
- [ ] GitHub Desktop
- [ ] Visual Studio Code
    - [ ] Pylance

However, what may work best for you might be different. 

### GitHub Desktop
GitHub Desktop is a free, user-friendly application that provides a visual interface for Git and GitHub. Instead of running Git commands in a terminal, GitHub Desktop lets you perform common tasks through an intuitive UI.

It allows you to:
- Clone, fork, and manage repositories without using the command line
- Easily create and switch branches
- Visualize commit history and branches in a clear, interactive timeline
- Stage and push local changes with a click
- Resolve merge conflicts with guided prompts

Overall, GitHub Desktop makes Git simpler, safer, and more visual, which is great for maintaining clean, branched pull requests and staying aligned with the rest of the Python SDK team.

### VS Studio Code
VS Code is a workpace that enables:

- Easy project navigation
- Easy file organisation
- Access to a large ecosystem of extensions that plug-in, including Pylance and GitHub Copilot

It’s the recommended editor for working within this SDK.

#### Pylance
Pylance is a high-performance language server for Python that:

- Improves code quality
- Identifies errors early
- Helps you resolve issues faster

For example, Pylance will underline this in red indicating it is incorrect with a reason:
```python
from hiero_sdk_python.account.token_id import TokenId
```
This is incorrect because token_id.py does not live in /account! Instead, it lives in /tokens

Read our [Pylance Installation Guide](../../pylance.md)



