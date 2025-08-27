 Testing The Hiero Python SDK

## Pytest Installation

Make sure to execute in the same Virtual Environment as the Project.

```bash
uv sync --group dev --group lint -v 
``` 
This installs pytest in the environment managed by uv and prints verbose.

## Running Tests

Once pytest is installed you can run the test suite in several ways.

### Run All Tests

```bash
uv run pytest
```

## Run Specific Test Types

by default, pytest runs all tests it finds. You can target specific folders:

### Unit tests only:

```bash
uv run pytest tests/unit
```

OR

```bash
uv run pytest tests/unit/specific_name.py
```
if you need to test one file.

### Integration tests only:

```bash
uv run pytest tests/integration
```

OR

```bash
pytest tests/integration
```
### What Are Unit vs. Integration Tests?

Unit tests check small, isolated parts of the SDK (e.g., one function or class) to ensure they behave correctly. They do not depend on external services.

Integration tests check how multiple parts work together with interaction with the Hedera testnet. They are run automatically using a github action `Solo action` when pushing to your repo.

#### Example:

Unit test: Verify that token amount formatting works correctly.

Integration test: Actually mint a token on the Hedera testnet and confirm it appears in an account.

## Run a Single File  or Test

Run a single file:
```bash
uv run pytest tests/unit/test_account_info.py
```

OR

```bash
pytest tests/unit/test_account_info.py
```

Run a single test inside that file:
```bash
uv run pytest tests/unit/test_account_info.py::test_proto_conversion
```

OR

```bash
pytest tests/unit/test_account_info.py::test_proto_conversion
```

## Interpreting Results
Pytest output looks something like this:

```
============================== test session starts ==============================
collected 12 items

tests/unit/test_account.py::test_create_account PASSED                   [  8%]
tests/unit/test_account.py::test_transfer_token FAILED                   [ 16%]

=================================== FAILURES ====================================
____________________________ test_transfer_token _______________________________

    def test_transfer_token():
>       assert transfer_token(...) == True
E       AssertionError: assert False == True

tests/unit/test_account.py:45: AssertionError
=========================== short test summary info =============================
FAILED tests/unit/test_account.py::test_transfer_token - AssertionError
========================= 1 failed, 11 passed in 2.12s =========================
```

### Key parts:
* PASSED: Test passed successfully.
* Failed Test: failed (see reason in the `FAILURES` section).
* collected X items: How many tests pytest found.
* [ 8%] progress through the test suite.
* FAILURES section Shows where and why the test failed.


## Continuous Integration (CI)
When you push to a branch, both the unit and integration tests run automatically via Hiero Solo Action

The Hiero Solo Action runs integration tests automatically when you push to a branch.

To trigger Solo Action in CI:

1. Commit your changes.

2. Push to any branch:
```bash
git push origin your-branch
```

GitHub Actions will pick it up, run both unit and integration tests, and display results in the Actions tab of the repository.

You must pass all tests for your PR to be merged.

If you only change code locally and don’t push, it won’t run — you’ll have to run integration tests manually (Solo action is generally more robust simultor, better to just use that)

If you have to run integration tests manually check [Integration tests](#integration-tests-only)

## Sample Test Output
Example console output from a successful run:
```
Account creation successful. New Account ID: 0.0.5025xxx
New Account Private Key: 228a06c363b0eb328434d51xxx...
New Account Public Key: 8f444e36e8926def492adxxx...
Token creation successful. Token ID: 0.0.5025xxx
Token association successful.
Token dissociation successful.
Token minting successful.
Token transfer successful.
Token freeze successful.
Token unfreeze successful.
Token deletion successful.
Topic creation successful.
Topic message submitted.
Topic update successful.
Topic deletion successful.
```

learn more:

[GitHub Marketplace](https://github.com/marketplace/actions/hiero-solo-action)
[Blog post by Hendrik Ebbers](https://dev.to/hendrikebbers/ci-for-hedera-based-projects-2nja)
