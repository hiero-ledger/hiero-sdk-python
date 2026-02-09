# Testing Guide for Hiero Python SDK Developers

## Introduction

Testing is an essential part of developing new functionality for the Hiero Python SDK. As a contributor, you are required to provide both **unit tests** and **integration tests** for any features you implement. This ensures code quality, prevents regressions, and maintains the reliability of the SDK.

**Unit tests** are lightweight, fast tests that verify individual components in isolation. They can be easily run on your local machine without requiring network connectivity.

**Integration tests** interact with an actual Hedera network (or a local Solo network) to verify that SDK components work correctly end-to-end. When you push a branch as a pull request, these tests automatically run against a Solo network in our CI pipeline.

This guide will walk you through:
- Understanding what unit and integration tests are
- Setting up your local testing environment
- Writing effective tests
- Running tests locally and in CI
- Best practices and common patterns

---

## Table of Contents

1. [Explaining Unit Tests](#explaining-unit-tests)
2. [Explaining Integration Tests](#explaining-integration-tests)
3. [Setting Up a Local Testing Suite](#setting-up-a-local-testing-suite)
   - [VS Code Setup](#vs-code-setup)
   - [Running from Bash/Terminal](#running-from-bashterminal)
4. [Running Integration Tests](#running-integration-tests)
5. [Writing Your First Test](#writing-your-first-test)
6. [Test Patterns and Best Practices](#test-patterns-and-best-practices)
7. [Common Testing Utilities](#common-testing-utilities)
8. [Troubleshooting](#troubleshooting)

---

## Explaining Unit Tests

### What Are Unit Tests?

Unit tests are automated tests that verify the behavior of **individual functions, classes, or methods** in isolation. They test the smallest testable parts of your code without external dependencies like network calls, databases, or file systems.

### Characteristics of Unit Tests

- **Fast**: Run in milliseconds
- **Isolated**: Test one component at a time
- **No External Dependencies**: Use mocks or stubs for dependencies
- **Deterministic**: Always produce the same result for the same input
- **Independent**: Can run in any order

### Example Unit Test Structure

```python
import pytest
from hiero_sdk_python.hbar import Hbar

def test_hbar_conversion_to_tinybars():
    """Test that Hbar correctly converts to tinybars."""
    hbar = Hbar(1)
    assert hbar.to_tinybars() == 100_000_000

def test_hbar_from_tinybars():
    """Test that Hbar can be created from tinybars."""
    hbar = Hbar.from_tinybars(200_000_000)
    assert hbar.to_tinybars() == 200_000_000
```

### When to Write Unit Tests

Write unit tests for:
- Data transformations and calculations
- Validation logic
- Utility functions
- Object constructors and property setters
- Serialization/deserialization logic
- Error handling paths

### Location of Unit Tests

Unit tests are located in the `tests/unit/` directory, mirroring the structure of the main codebase:

```
hiero-sdk-python/
├── src/hiero_sdk_python/
│   ├── account/
│       └── account_create_transaction.py
└── tests/
    └── unit/
        └── test_account_create_transaction.py
```
---

## Explaining Integration Tests

### What Are Integration Tests?

Integration tests verify that **multiple components work together correctly** and that the SDK successfully interacts with a Hedera network. These tests execute actual transactions and queries against a running network.

### Characteristics of Integration Tests

- **Slower**: Take seconds or minutes to run
- **Network-Dependent**: Require connection to a Hedera network
- **End-to-End**: Test complete workflows
- **Resource-Consuming**: Use real HBAR, gas, and network resources
- **Sequential**: Some tests may depend on network state

### Example Integration Test Structure

```python
import pytest
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils import IntegrationTestEnv


@pytest.mark.integration
def test_integration_account_create_transaction_can_execute():
   """Test that an account can be created on the network."""
   env = IntegrationTestEnv()
   try:
      new_account_private_key = PrivateKey.generate()
      new_account_public_key = new_account_private_key.public_key()
      initial_balance = Hbar(2)

      transaction = AccountCreateTransaction(
         key=new_account_public_key,
         initial_balance=initial_balance,
         memo="Test Account"
      )
      transaction.freeze_with(env.client)
      receipt = transaction.execute(env.client)

      assert receipt.account_id is not None, "Account ID should be present"
      assert receipt.status == ResponseCode.SUCCESS
   finally:
      env.close()
```

### When to Write Integration Tests

Write integration tests for:
- Transaction execution (create, update, delete operations)
- Query operations (balance, info queries)
- Complex workflows involving multiple steps
- Network-specific behavior
- Error responses from the network
- Fee calculations

### Location of Integration Tests

Integration tests are located in the `tests/integration/` directory:

```
hiero-sdk-python/
└── tests/
    └── integration/
        ├── account_create_transaction_e2e_test.py
        ├── account_delete_transaction_e2e_test.py
        ├── contract_execute_transaction_e2e_test.py
        └── utils_for_test.py
```

### Integration Test Naming Convention

Integration test files should follow the pattern: `<feature>_e2e_test.py`

For example:
- `account_allowance_e2e_test.py`
- `token_associate_transaction_e2e_test.py`
- `contract_call_query_e2e_test.py`

---

## Setting Up a Local Testing Suite

### Prerequisites

Before setting up your testing environment, ensure you have:

1. **Python 3.10+** installed
2. **uv** package manager installed (recommended)
3. **Git** for version control
4. A code editor (VS Code recommended)

### Installation Steps

#### 1. Clone the Repository

```bash
git clone https://github.com/hiero-ledger/hiero-sdk-python.git
cd hiero-sdk-python
```

#### 2. Install Dependencies with uv

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or on macOS with Homebrew
brew install uv

# Install project dependencies
uv sync

# Generate protobuf files
uv run python generate_proto.py
```

The `uv sync` command automatically:
- Downloads the correct Python version
- Creates a virtual environment
- Installs all dependencies including `pytest` and testing tools

#### 3. Configure Environment Variables

Create a `.env` file in the project root with your Hedera testnet credentials:

```bash
# Required
OPERATOR_ID=0.0.1234567
OPERATOR_KEY=302e020100300506032b657004220420...
NETWORK=testnet

# Optional (for specific tests)
ADMIN_KEY=302e020100300506032b657004220420...
SUPPLY_KEY=302a300506032b6570032100...
FREEZE_KEY=302a300506032b6570032100...
RECIPIENT_ID=0.0.7891011
TOKEN_ID=0.0.1234568
TOPIC_ID=0.0.1234569
```

**Note**: A sample `.env.example` file is provided. If you don't have a testnet account, create one at [Hedera Portal](https://portal.hedera.com/).

---

### VS Code Setup

VS Code provides excellent Python testing support with built-in test discovery and debugging.

#### 1. Install Python Extension

Install the official **Python extension** by Microsoft from the VS Code marketplace.

#### 2. Configure Testing

1. Open the Command Palette (`Cmd+Shift+P` on macOS, `Ctrl+Shift+P` on Windows/Linux)
2. Type "Python: Configure Tests"
3. Select **pytest** as the test framework
4. Select **tests** as the directory containing tests

#### 3. Discover Tests

- Click the **Testing** icon in the Activity Bar (flask icon)
- VS Code will automatically discover all tests marked with `@pytest.mark.*`
- Tests will be organized by file and function

#### 4. Run Tests from VS Code

**Run All Tests:**
- Click "Run All Tests" button in the Testing panel

**Run Individual Test:**
- Hover over a test function
- Click the green play button

**Run Test File:**
- Right-click on a test file
- Select "Run Tests"

**Debug Tests:**
- Click the debug icon next to any test
- Set breakpoints in your code
- Step through execution

#### 5. View Test Results

- Test results appear in the Testing panel
- Failed tests show error messages and stack traces
- Click on a failed test to jump to the code

#### 6. VS Code Settings (Optional)

Add to `.vscode/settings.json`:

```json
{
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.pytestArgs": [
    "tests"
  ],
  "python.testing.autoTestDiscoverOnSaveEnabled": true
}
```

---

### Running from Bash/Terminal

You can run tests directly from the command line, which is useful for CI/CD and quick local verification.

#### Run All Tests

```bash
# Using uv (recommended)
uv run pytest

# Or activate the virtual environment first
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pytest
```

#### Run Only Unit Tests

```bash
uv run pytest tests/unit/
```

#### Run Only Integration Tests

```bash
uv run pytest tests/integration/
# Or using the marker:
uv run pytest -m integration
```

#### Run Specific Test File

```bash
uv run pytest tests/unit/hbar_test.py
```

#### Run Specific Test Function

```bash
uv run pytest tests/unit/hbar_test.py::test_hbar_conversion_to_tinybars
```

#### Run Tests with Verbose Output

```bash
uv run pytest -v
```

#### Run Tests with Output Capture Disabled

```bash
uv run pytest -s
```

#### Run Tests and Show Local Variables on Failure

```bash
uv run pytest -l
```

#### Run Tests with Coverage Report

```bash
uv run pytest --cov=hiero_sdk_python --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html`.

#### Run Tests in Parallel (Faster)

```bash
# Install pytest-xdist first
uv pip install pytest-xdist

# Run tests in parallel
uv run pytest -n auto
```

#### Common pytest Options

| Option | Description |
|--------|-------------|
| `-v` or `--verbose` | Increase verbosity |
| `-s` | Don't capture output (show print statements) |
| `-x` | Stop on first failure |
| `--lf` | Run last failed tests only |
| `--ff` | Run failures first, then the rest |
| `-k <expression>` | Run tests matching expression |
| `-m <marker>` | Run tests with specific marker |
| `--collect-only` | Show available tests without running |

---

## Running Integration Tests

Integration tests require connection to a Hedera network. There are three ways to run them:

### 1. Against Testnet (Recommended for Local Development)

**Requirements:**
- Testnet account with HBAR balance
- Valid `.env` configuration

**Command (Recommended - use Solo network):**
```bash
# Start your local Solo network first
solo network start

# Then run integration tests
uv run pytest tests/integration/ -m integration
```

**Considerations:**
- Uses real HBAR (small amounts)
- Tests run against actual Hedera testnet
- Slower due to consensus time
- May fail if network is congested

### 2. In CI/CD (Automatic)

When you push a branch and create a pull request, integration tests automatically run via GitHub Actions using the **Hiero Solo Action**.

**Workflow:**
1. Push your branch: `git push origin your-branch-name`
2. Create a pull request
3. GitHub Actions automatically:
   - Starts a Solo network
   - Runs all integration tests
   - Reports results in the PR

**Viewing Results:**
- Go to your PR on GitHub
- Click "Checks" tab
- View test results and logs

**CI Configuration** is in `.github/workflows/` (you don't need to modify this).

---

## Writing Your First Test

Let's walk through creating both unit and integration tests for a hypothetical new feature.

### Example: Testing a New Token Transfer Function

#### 1. Create Unit Test

**File:** 
You may look at an already-created unit test file for better clarity:
[token_pause_transaction_test.py](../../tests/unit/token_pause_transaction_test.py)


#### 2. Create Integration Test

**File:**
You may look at an already-created unit test file for better clarity:
[token_pause_transaction_e2e_test.py](../../tests/integration/token_pause_transaction_e2e_test.py)

#### 3. Run Your Tests

```bash
# Run unit tests
uv run pytest tests/unit/tokens/token_transfer_test.py -v

# Run integration tests
uv run pytest tests/integration/token_transfer_e2e_test.py -v
```

---

## Test Patterns and Best Practices

### General Testing Principles

#### 1. **AAA Pattern (Arrange, Act, Assert)**

Structure your tests clearly:

```python
def test_example():
    # Arrange - Set up test data and preconditions
    account_id = AccountId(0, 0, 1001)
    initial_balance = Hbar(10)
    
    # Act - Perform the action being tested
    result = calculate_new_balance(account_id, initial_balance)
    
    # Assert - Verify the outcome
    assert result.to_tinybars() == 1_000_000_000
```

#### 2. **Test One Thing at a Time**

Each test should verify a single behavior:

```python
# Good - Tests one specific behavior
def test_hbar_to_tinybars_conversion():
    hbar = Hbar(1)
    assert hbar.to_tinybars() == 100_000_000

# Bad - Tests multiple behaviors
def test_hbar_everything():
    hbar = Hbar(1)
    assert hbar.to_tinybars() == 100_000_000
    assert hbar.from_tinybars(200_000_000).to_tinybars() == 200_000_000
    assert Hbar(5).to_tinybars() == 500_000_000
```

#### 3. **Use Descriptive Test Names**

Test names should describe what is being tested:

```python
# Good
def test_account_create_fails_with_insufficient_balance():
    pass

# Bad
def test_account():
    pass
```

#### 4. **Write Independent Tests**

Tests should not depend on each other:

```python
# Bad - Tests depend on execution order
account = None

def test_create_account():
    global account
    account = create_account()

def test_update_account():
    update_account(account)  # Depends on previous test

# Good - Each test is independent
def test_create_account():
    account = create_account()
    assert account is not None

def test_update_account():
    account = create_account()  # Create fresh account
    result = update_account(account)
    assert result is True
```

### Unit Test Best Practices

#### 1. **Mock External Dependencies**

```python
from unittest.mock import Mock, patch

def test_transaction_execution_calls_network():
    """Test that transaction execution calls the network correctly."""
    mock_client = Mock()
    mock_client.execute.return_value = {"status": "SUCCESS"}
    
    transaction = SomeTransaction()
    result = transaction.execute(mock_client)
    
    mock_client.execute.assert_called_once()
    assert result["status"] == "SUCCESS"
```

#### 2. **Test Edge Cases**

```python
def test_hbar_handles_zero():
    hbar = Hbar(0)
    assert hbar.to_tinybars() == 0

def test_hbar_handles_large_values():
    hbar = Hbar(1_000_000)
    assert hbar.to_tinybars() == 100_000_000_000_000

def test_hbar_handles_negative_values():
    with pytest.raises(ValueError):
        Hbar(-1)
```

#### 3. **Use Fixtures for Common Setup**

```python
import pytest

@pytest.fixture
def sample_account_id():
    """Provide a sample account ID for tests."""
    return AccountId(0, 0, 1001)

@pytest.fixture
def sample_token_id():
    """Provide a sample token ID for tests."""
    return TokenId(0, 0, 12345)

def test_with_fixtures(sample_account_id, sample_token_id):
    """Test using pytest fixtures."""
    transfer = create_transfer(sample_account_id, sample_token_id, 100)
    assert transfer.account_id == sample_account_id
```

### Integration Test Best Practices

#### 1. **Use the `env` Fixture**

The `env` fixture from `utils_for_test.py` provides a configured test environment:

```python
from tests.integration.utils import env


@pytest.mark.integration
def test_with_env_fixture(env):
   """Test using the env fixture."""
   # env.client is already configured
   # env.operator_id and env.operator_key are available
   account = env.create_account()  # Helper method
   assert account.id is not None
```

#### 2. **Always Clean Up Resources**

```python
@pytest.mark.integration
def test_with_cleanup(env):
    """Test with proper cleanup."""
    account = None
    try:
        account = env.create_account()
        # Perform test operations
        assert account.id is not None
    finally:
        # Clean up if necessary
        if account:
            # Delete account or release resources
            pass
```

#### 3. **Test Both Success and Failure Cases**

```python
@pytest.mark.integration
def test_account_create_succeeds(env):
    """Test successful account creation."""
    receipt = create_account(env)
    assert receipt.status == ResponseCode.SUCCESS

@pytest.mark.integration
def test_account_create_fails_with_invalid_key(env):
    """Test that account creation fails with invalid key."""
    receipt = create_account_with_invalid_key(env)
    assert receipt.status == ResponseCode.INVALID_SIGNATURE
```

#### 4. **Use Helper Functions**

Extract common setup into helper functions:

```python
def _create_and_associate_token(env, account):
    """Helper to create token and associate it with account."""
    token_receipt = TokenCreateTransaction().execute(env.client)
    token_id = token_receipt.token_id
    
    TokenAssociateTransaction().set_account_id(account.id).add_token_id(token_id).execute(env.client)
    
    return token_id

@pytest.mark.integration
def test_token_transfer(env):
    sender = env.create_account()
    receiver = env.create_account()
    token_id = _create_and_associate_token(env, receiver)
    # Continue with test...
```

#### 5. **Verify Transaction Status**

Always check that transactions succeed:

```python
receipt = transaction.execute(env.client)
assert receipt.status == ResponseCode.SUCCESS, (
    f"Transaction failed with status: {ResponseCode(receipt.status).name}"
)
```

### Testing Error Handling

#### 1. **Test Expected Exceptions**

```python
import pytest
from hiero_sdk_python.exceptions import PrecheckError

def test_invalid_account_raises_error():
    """Test that invalid account ID raises appropriate error."""
    with pytest.raises(PrecheckError, match="INVALID_ACCOUNT_ID"):
        query_invalid_account()
```

#### 2. **Test Response Codes**

```python
@pytest.mark.integration
def test_insufficient_balance_error(env):
    """Test that insufficient balance returns correct response code."""
    receipt = transfer_more_than_balance(env)
    assert receipt.status == ResponseCode.INSUFFICIENT_ACCOUNT_BALANCE
```

---

## Common Testing Utilities

### The `utils_for_test.py` File

The `tests/integration/utils_for_test.py` file provides essential testing utilities:

#### IntegrationTestEnv Class

```python
from tests.integration.utils import IntegrationTestEnv, env

# Create environment manually
env = IntegrationTestEnv()
try:
   # Use env.client, env.operator_id, env.operator_key
   pass
finally:
   env.close()


# Or use the pytest fixture (recommended)
@pytest.mark.integration
def test_example(env):
   # env is automatically created and cleaned up
   account = env.create_account()
```

**Key Methods:**
- `env.create_account()` - Creates a new test account with 1 HBAR
- `env.client` - Configured Hedera client
- `env.operator_id` - Operator account ID
- `env.operator_key` - Operator private key
- `env.close()` - Cleanup (automatic with fixture)

#### Helper Functions

```python
from tests.integration.utils import (
   create_fungible_token,
   create_nft_token,
   env
)


@pytest.mark.integration
def test_with_helpers(env):
   # Create a fungible token with default settings
   token_id = create_fungible_token(env)

   # Create an NFT token
   nft_id = create_nft_token(env)

   # Use custom configuration with lambdas
   token_id = create_fungible_token(env, [
      lambda tx: tx.set_decimals(8),
      lambda tx: tx.set_initial_supply(1000000)
   ])
```

### Pytest Markers

Use markers to categorize tests:

```python
# Mark as integration test
@pytest.mark.integration
def test_network_operation(env):
    pass

# Mark as slow test
@pytest.mark.slow
def test_long_running_operation():
    pass

# Skip test conditionally
@pytest.mark.skipif(condition, reason="Reason for skipping")
def test_conditional():
    pass
```

Run specific markers:
```bash
# Run only integration tests
uv run pytest -m integration

# Run everything except slow tests
uv run pytest -m "not slow"
```

### Parametrized Tests

Test multiple inputs efficiently:

```python
@pytest.mark.parametrize("amount,expected", [
    (1, 100_000_000),
    (5, 500_000_000),
    (10, 1_000_000_000),
    (0, 0),
])
def test_hbar_conversions(amount, expected):
    """Test Hbar to tinybar conversions with different values."""
    hbar = Hbar(amount)
    assert hbar.to_tinybars() == expected
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: Tests Not Discovered by pytest

**Symptoms:**
- Running `pytest` shows "no tests ran"
- VS Code doesn't show tests in Testing panel

**Solutions:**
1. Ensure test files start with `test_` or end with `_test.py`
2. Ensure test functions start with `test_`
3. Check that `pytest` is installed: `uv pip list | grep pytest`
4. Verify you're in the correct directory: `pwd` should show project root
5. Clear pytest cache: `uv run pytest --cache-clear`

#### Issue: Integration Tests Fail with Connection Error

**Symptoms:**
```
ConnectionError: Failed to connect to network
```

**Solutions:**
1. Verify `.env` file exists and contains valid credentials
2. Check network connectivity: `ping testnet.hedera.com`
3. Verify `NETWORK` environment variable is set correctly
4. Ensure operator account has sufficient HBAR balance
5. Try using a different network node

#### Issue: Integration Tests Fail with INSUFFICIENT_TX_FEE

**Symptoms:**
```
PrecheckError: Transaction failed precheck with status: INSUFFICIENT_TX_FEE
```

**Solutions:**
1. Check operator account balance
2. Increase max transaction fee if needed
3. Verify transaction is properly configured
4. Check if network fees have increased

#### Issue: Tests Pass Locally but Fail in CI

**Symptoms:**
- Tests pass on your machine
- Same tests fail in GitHub Actions

**Solutions:**
1. Check CI logs for specific error messages
2. Verify environment variables are set in CI
3. Check for timing issues (add waits if needed)
4. Ensure Solo network is properly configured
5. Check for network-specific behavior differences

#### Issue: Tests Are Too Slow

**Symptoms:**
- Tests take minutes to run
- Integration tests timeout

**Solutions:**
1. Run only unit tests during development: `uv run pytest tests/unit/`
2. Use pytest-xdist for parallel execution: `uv run pytest -n auto`
3. Mark slow tests and exclude them: `uv run pytest -m "not slow"`
4. Use Solo network instead of testnet for faster consensus
5. Optimize test setup - reuse accounts/tokens when possible

#### Issue: Import Errors in Tests

**Symptoms:**
```
ModuleNotFoundError: No module named 'hiero_sdk_python'
```

**Solutions:**
1. Ensure virtual environment is activated
2. Reinstall in editable mode: `uv pip install -e .`
3. Generate protobuf files: `uv run python generate_proto.py`
4. Check Python path: `python -c "import sys; print(sys.path)"`

#### Issue: Flaky Integration Tests

**Symptoms:**
- Tests pass sometimes, fail other times
- Inconsistent results

**Solutions:**
1. Add proper waits for network consensus
2. Don't assume immediate state changes
3. Query network state to verify before assertions
4. Avoid hard-coded delays, use polling instead
5. Ensure proper test isolation

#### Issue: Mock Not Working in Unit Tests

**Symptoms:**
- Mocked functions are being called for real
- Mock assertions fail

**Solutions:**
1. Ensure you're patching the correct path (where it's used, not where it's defined)
2. Use `patch` as decorator or context manager correctly
3. Verify mock is applied before the code runs
4. Check import statements in test file

Example:
```python
# Wrong - patches where defined
@patch('hiero_sdk_python.client.Client.execute')
def test_wrong():
    pass

# Correct - patches where used
@patch('my_module.Client.execute')
def test_correct():
    pass
```

#### Issue: Environment Variables Not Loading

**Symptoms:**
- Tests can't find operator credentials
- `None` values for env variables

**Solutions:**
1. Verify `.env` file is in project root
2. Check file permissions: `ls -la .env`
3. Ensure `python-dotenv` is installed
4. Load manually in test if needed:
```python
from dotenv import load_dotenv
load_dotenv()
```

#### Issue: Test Database/State Pollution

**Symptoms:**
- Tests fail when run together but pass individually
- Test order matters

**Solutions:**
1. Use unique identifiers for each test
2. Clean up resources in `finally` blocks
3. Use pytest fixtures with appropriate scope
4. Avoid global state
5. Create fresh accounts/tokens per test

---

## Advanced Testing Techniques

### Mocking Network Responses

For unit tests that need to simulate network behavior:

```python
from unittest.mock import Mock, patch
import pytest
from hiero_sdk_python.response_code import ResponseCode

def test_transaction_handles_network_error():
    """Test that transaction properly handles network errors."""
    mock_client = Mock()
    mock_client.execute.side_effect = Exception("Network timeout")
    
    transaction = SomeTransaction()
    
    with pytest.raises(Exception, match="Network timeout"):
        transaction.execute(mock_client)

def test_transaction_retries_on_failure():
    """Test that transaction retries on transient failures."""
    mock_client = Mock()
    # First call fails, second succeeds
    mock_client.execute.side_effect = [
        {"status": ResponseCode.BUSY},
        {"status": ResponseCode.SUCCESS}
    ]
    
    transaction = SomeTransaction()
    result = transaction.execute_with_retry(mock_client, max_retries=2)
    
    assert result["status"] == ResponseCode.SUCCESS
    assert mock_client.execute.call_count == 2
```

### Testing Async Code

If your SDK has async functionality:

```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_async_transaction():
    """Test asynchronous transaction execution."""
    client = await create_async_client()
    
    transaction = AsyncTransaction()
    result = await transaction.execute(client)
    
    assert result.status == ResponseCode.SUCCESS
```

### Property-Based Testing

Use hypothesis for property-based testing:

```python
from hypothesis import given, strategies as st

@given(st.integers(min_value=0, max_value=1000000))
def test_hbar_conversion_property(amount):
    """Test that Hbar conversion is consistent for any valid amount."""
    hbar = Hbar(amount)
    tinybars = hbar.to_tinybars()
    hbar2 = Hbar.from_tinybars(tinybars)
    
    assert hbar.to_tinybars() == hbar2.to_tinybars()
```

### Snapshot Testing

For complex output verification:

```python
def test_transaction_serialization_snapshot(snapshot):
    """Test that transaction serialization hasn't changed."""
    transaction = create_test_transaction()
    serialized = transaction.to_proto()
    
    # Compare against saved snapshot
    snapshot.assert_match(serialized)
```

### Performance Testing

Test performance characteristics:

```python
import time

def test_transaction_performance():
    """Test that transaction creation is fast."""
    start = time.time()
    
    for _ in range(1000):
        transaction = AccountCreateTransaction()
    
    duration = time.time() - start
    assert duration < 1.0, f"Transaction creation took {duration}s, expected < 1s"
```

### Coverage Analysis

Check test coverage:

```bash
# Generate coverage report
uv run pytest --cov=hiero_sdk_python --cov-report=html --cov-report=term

# View in browser
open htmlcov/index.html
```

Aim for:
- **80%+ overall coverage**
- **100% coverage for critical paths** (transaction execution, signing)
- **90%+ coverage for new features**

---

## Testing Checklist for Contributors

Before submitting a pull request, ensure:

### Unit Tests
- [ ] All new functions/methods have unit tests
- [ ] Edge cases are covered
- [ ] Error handling is tested
- [ ] Tests use mocks for external dependencies
- [ ] Tests run in < 5 seconds total
- [ ] All unit tests pass: `uv run pytest tests/unit/`

### Integration Tests
- [ ] E2E workflow tests are included
- [ ] Both success and failure cases are tested
- [ ] Tests are marked with `@pytest.mark.integration`
- [ ] Tests clean up resources properly
- [ ] Tests use the `env` fixture
- [ ] All integration tests pass: `uv run pytest tests/integration/`

### Code Quality
- [ ] Tests follow naming conventions
- [ ] Test functions have clear docstrings
- [ ] Code is formatted with `ruff`: `uv run ruff format`
- [ ] No linting errors: `uv run ruff check`
- [ ] Test coverage is adequate

### Documentation
- [ ] `CHANGELOG.md` is updated under `UNRELEASED`
- [ ] Complex test logic is commented
- [ ] Test fixtures are documented

### Git
- [ ] Commits are signed: `git commit -S -s -m "chore: message"` (Add a scope prefix to your chore: commit message to match the project’s commit message style guide)
- [ ] Commits are verified: `git log --show-signature`
- [ ] Branch is up to date with `main`

---

## Example Test Files Reference

### Simple Unit Test Example

**File:** [account_id_test.py](../../tests/unit/account_id_test.py)

### Simple Integration Test Example

**File:** [account_balance_query_e2e_test.py](../../tests/integration/account_balance_query_e2e_test.py)

### Complex Integration Test Example

See the provided `tests/integration/account_allowance_e2e_test.py` for examples of:
- Setting up complex test scenarios
- Using helper functions
- Testing multiple related operations
- Verifying both success and failure paths
- Testing allowances, approvals, and delegations

---

## Best Practices Summary

### DO ✅

- **Write tests for all new features**
- **Test both success and failure paths**
- **Use descriptive test names**
- **Keep tests focused and independent**
- **Use fixtures for common setup**
- **Mock external dependencies in unit tests**
- **Clean up resources in integration tests**
- **Verify transaction status codes**
- **Document complex test logic**
- **Run tests before committing**
- **Sign your commits**
- **Update CHANGELOG.md**

### DON'T ❌

- **Don't skip writing tests**
- **Don't test multiple things in one test**
- **Don't create test dependencies**
- **Don't use hard-coded sleeps**
- **Don't commit commented-out tests**
- **Don't ignore failing tests**
- **Don't forget to test error cases**
- **Don't leak resources in integration tests**
- **Don't use real production credentials**
- **Don't forget to update documentation**

---

## Getting Help

If you encounter issues or have questions:

1. **Check this guide** - Most common scenarios are covered
2. **Review existing tests** - Look at similar tests in the codebase
3. **Check documentation** - See [`/docs/sdk_developers/`](./)
4. **Ask in Discord** - Ask on the [Linux Foundation Decentralized Trust Discord](https://discord.gg/hyperledger)
5. **Open an issue** - For bugs or unclear documentation

### Useful Resources

- **Contributing Guide**: [CONTRIBUTING.md](../../CONTRIBUTING.md)
- **Commit Signing Guide**: [signing.md](signing.md)
- **pytest Documentation**: https://docs.pytest.org/
- **Hedera Documentation**: https://docs.hedera.com/
- **Hiero Solo**: https://github.com/hiero-ledger/solo

---

## Conclusion

Testing is a critical part of SDK development. By writing comprehensive unit and integration tests, you ensure:

- **Code Quality** - Catch bugs early
- **Maintainability** - Refactor with confidence
- **Documentation** - Tests show how code should be used
- **Reliability** - Users can trust the SDK

Remember:
1. **Unit tests** verify individual components in isolation
2. **Integration tests** verify end-to-end workflows with real network
3. Run tests locally before pushing
4. All tests must pass in CI before merging

Thank you for contributing to the Hiero Python SDK! Your tests make the SDK better for everyone.