## Breaking Changes and the Python SDK

Breaking changes are generally not acceptable in Python SDK development. This is because they can:
- Stop existing Python SDK users’ code from working
- Force users to spend time and resources updating their applications
- Remove functionality that users may rely on, with no equivalent replacement

Breaking changes damage trust with our users and should be avoided whenever possible.

### Identifying Whether Your Pull Request Introduces a Breaking Change

Even if an issue does not mention breaking changes, a pull request may still introduce one.

Common examples include:
- Removing or renaming an existing function or class
- Changing the return type or structure of a function or method
- Modifying the parameters a function accepts (adding, removing, or changing types)
- Refactoring a function or class in a way that changes its behaviour, even subtly
- Changing default values or altering side effects

When preparing a pull request, always evaluate whether any existing user code would stop working as a result of your changes even if its 'better'.

For example - before:
```python
def transfer_tokens(account_id: str, amount: int):
    ...
```

For example - after - breaking:
```python
def transfer_tokens(account_id: AccountId, amount: int, memo: str = None):
    ...
```
User code passing a string account_id now fails, and adding a required memo parameter breaks all existing calls.


## What to Do If a Breaking Change Is Unavoidable

Breaking changes should be avoided, but in rare cases they are necessary.

Examples include:
- Correcting significant errors or faulty behaviour
- Implementing new standards or APIs (such as HIPS)
- Replacing deprecated functionality that cannot be maintained

If a breaking change must occur:
- Document it in the pull request
- When possible, implement or propose backwards compatibility solutions (deprecation warnings, transitional methods, alternative APIs, etc.).

Example pull request description:

`BREAKING CHANGE: transfer_tokens() now requires an AccountId object instead of a string.`


Breaking changes are typically scheduled for major releases, giving users time to prepare and migrate safely.
