# Hiero Python SDK Project Structure

Welcome to the Hiero Python SDK! Understanding the repository's structure is the first step to contributing effectively. This guide outlines the main directories and explains where to find the core SDK functionality, helping you locate the classes and methods you need to use and modify.

## Table of Contents

- [Top-Level File Structure](#top-level-file-structure)
  - [The `docs` Directory](#the-docs-directory)
  - [The `examples` Directory](#the-examples-directory)
  - [The `src` Directory (Core SDK)](#the-src-directory-core-sdk)
  - [The `tests` Directory](#the-tests-directory)
- [Implications for Development (How to Import)](#implications-for-development-how-to-import)
- [Conclusion](#conclusion)

---

## Top-Level File Structure

The repository is organized into four main directories:

- `/docs`: All project documentation.
- `/examples`: Runnable example scripts for SDK users.
- `/src`: The SDK source code. **This is where you will make code changes.**
- `/tests`: The unit and integration tests for the SDK.

### The `docs` Directory

This directory contains all documentation for both users and developers of the SDK.

-   **`docs/sdk_users/`**: Guides for people *using* the SDK in their applications (e.g., `running_examples.md`).
-   **`docs/sdk_developers/`**: Guides for people *contributing* to the SDK (e.g., `CONTRIBUTING.md`, `signing.md`, `testing.md`).

### The `examples` Directory

This folder contains complete, runnable Python scripts demonstrating how to use the SDK for various operations, such as creating tokens or submitting topic messages. This is the best place to see the SDK in action.

### The `src` Directory (Core SDK)

This is the heart of the SDK. The main source code lives inside `src/hiero_sdk_python/`. As an SDK developer, you will spend most of your time reading and modifying files in this directory.

#### `src/hiero_sdk_python/hapi`

This directory contains the Python classes auto-generated from the Hedera `.proto` (protobuf) files.

-   **Do not edit files here!** They are generated automatically by running `uv run python generate_proto.py`.
-   This is an advanced concept, but it can be useful to look at these files (especially in `hapi/services/`) to understand the exact data structures required by the Hedera network APIs.

#### Core SDK Modules

The other directories inside `src/hiero_sdk_python/` contain the actual SDK logic. This is where you will add features, fix bugs, and make your contributions.

Each directory corresponds to a specific area of functionality:

-   **`account/`**: Contains transactions and queries related to Hedera accounts (e.g., `AccountCreateTransaction`, `AccountInfoQuery`).
-   **`address_book/`**: Contains logic for node address books.
-   **`client/`**: Contains the main `Client` class that manages network connections and operators.
-   **`consensus/`**: For Hedera Consensus Service (HCS) (e.g., `TopicCreateTransaction`, `TopicMessageSubmitTransaction`).
-   **`contract/`**: For Hedera Smart Contract Service (HSCS) (e.g., `ContractCreateTransaction`, `ContractCallQuery`).
-   **`file/`**: For Hedera File Service (HFS) (e.g., `FileCreateTransaction`, `FileContentsQuery`).
-   **`logger/`**: Internal logging utilities.
-   **`nodes/`**: Transactions for managing network nodes (privileged operations).
-   **`query/`**: Base classes and logic for all network queries.
-   **`schedule/`**: For the Hedera Schedule Service (e.g., `ScheduleCreateTransaction`).
-   **`tokens/`**: For Hedera Token Service (HTS) (e.g., `TokenCreateTransaction`, `CustomFixedFee`).
-   **`transaction/`**: Base classes and logic for all network transactions.
-   **`utils/`**: Helper utilities, like for checksums or entity ID parsing.

There are also individual files (e.g., `Duration.py`, `channels.py`, `exceptions.py`, `hbar.py`) that provide utility classes.

When you work on an issue, you will most likely be modifying a file within one of these directories, such as `src/hiero_sdk_python/tokens/custom_fixed_fee.py`. Each file contains the specific logic for the services we provide for the Hedera network.

### The `tests` Directory

This directory contains all the automated tests for the SDK, separated into two main types:

-   **`tests/unit/`**: Unit tests that check individual functions and classes in isolation. They are fast and do not require a network connection.
-   **`tests/integration/`**: Integration tests that run end-to-end workflows against a live Hedera network (or a local `solo` network). These are marked with `@pytest.mark.integration`.

All contributions require new or updated tests to be included.

---

## Implications for Development (How to Import)

When you create a new feature (e.g., an imaginary `src/hiero_sdk_python/fees/step_fee.py`), you will need to import and use classes and functions from other modules.

For example, your new "step fee" logic might need:
-   `AccountId` (from `account/`) to know who pays and who receives the fee.
-   `TokenId` (from `tokens/`) if the fee is paid with a token.
-   The `Client` (from `client/`) to make network calls.

This is why every file begins with an import block. These imports must be correct and point to the exact location of the file within the `src/` directory.

### Finding the Correct Import Path

The import path always starts from the root of the package, `hiero_sdk_python`.

**Example 1: Importing the `TokenId` class**
-   **File Location:** `src/hiero_sdk_python/tokens/token_id.py`
-   **Class Name:** `TokenId`
-   **Correct Import:** `from hiero_sdk_python.tokens.token_id import TokenId`

**Example 2: Importing a Protobuf type**
-   **File Location:** `src/hiero_sdk_python/hapi/services/basic_types_pb2.py`
-   **File to Import:** `basic_types_pb2`
-   **Correct Import:** `from hiero_sdk_python.hapi.services import basic_types_pb2`

A tool like Pylance (in VS Code) can help verify your import paths and flag any that are incorrect.

---

## Conclusion

This guide outlines the basic file structure of the project. By understanding where different types of code live (`src/`, `tests/`, `examples/`, `docs/`), you can more easily find the classes you need to import and know where to place your new contributions.