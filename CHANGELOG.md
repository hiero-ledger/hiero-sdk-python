# Changelog

All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](https://semver.org).
This changelog is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Tests
- Standardize formatting of `tests/unit/entity_id_helper_test.py` using Black for consistent code style across the test suite (#1527)

- Added tests for ProtoBuf Training Example Implementation
- Formatted `tests/unit/get_receipt_query_test.py` with black for code style consistency. (#1537)
- format black `tests/unit/hbar*.py`.(#1538)
- Formatted `tests/unit/conftest.py` with black for code style consistency. (#1522)
- format `black tests/unit/nft_id_test.py` with Black.(#1544)
- Format `tests/unit/executable_test.py` with Black.(#1530)
- Format `tests/unit/hedera_trust_manager_test.py` with Black for consistent code style (#1539)
- Format tests/unit/logger_test.py with black for code style consistency (#1541)
- Format `tests/unit/batch_transaction_test.py` with Black.(`#1520`)
- Style: formatted `tests/unit/prng_transaction_test.py` with black (#1546)
- Formatted contract unit tests with black for consistent style. (#1523)
- Format account test files with Black (#1519)
- Format `tests/unit/node*.py` with Black for consistent code style (#1545)
- Improve unit test coverage for Hbar, including edge cases, validation, comparisons, and hashing. (#1483)
- Standardize formatting of evm_address_test.py using Black for improved consistency and readability (#1529)
- Formatted unit test files using Black.
- Format tests/unit/network_tls_test.py with black for code style consistency (#1543)
- Formatted `ethereum_transaction_test.py` using Black.
- Formatted client_test.py using Black.
- Format tests/unit/query*.py using black (#1547)
- Format `tests/unit/custom_fee_test.py` with black for code style consistency. (#1525)

### Added
- Added logging in bot-gfi-assign-on-comment.js to prevent silent skips. (`#1668`)
- Added `AssessedCustomFee` domain model to represent assessed custom fees. (`#1637`)
- Add __repr__ method for ContractId class to improve debugging (#1714)
- Added Protobuf Training guide to enhance developer understanding of proto serialization
  and deserialization (#1645)
- Add `__repr__()` method to `TopicId` class for improved debugging with constructor-style representation (#1629)
- Added guide for resolving CHANGELOG.md conflicts using GitHub's web editor (`#1591`)
- Added Windows setup guide for SDK developers (`docs/sdk_developers/training/setup/setup_windows.md`) with PowerShell installation instructions. (#1570)
- Added a beginner assignment guard that requires completion of a Good First Issue. (#1484)
- Added `/unassign` command allowing contributors to remove themselves from assigned issues.(#1472)
- Added advanced CodeRabbit reviewer guidance for `tokens` module changes, with specialized validation rules for token transactions, token classes, and enums. (#1496)
- Advanced-check bot unassigns users from issues if they do not meet the requirements and provides an explanatory message. (#1477)
- Auto-assignment bot for beginner-labeled issues with `/assign` command support and helpful reminders. (#1368)
- Added comprehensive docstring to `FeeAssessmentMethod` enum explaining inclusive vs exclusive fee assessment methods with usage examples. (#1391)
- Added comprehensive docstring to `TokenType` enum explaining fungible vs non-fungible tokens with practical use cases. (#1392)
- Enable dry run support for office hours bot via `workflow_dispatch` trigger for testing without posting comments. (#1426)
- Trigger CodeRabbit plan comment after Good First Issue assignment to provide AI-generated implementation guidance to new contributors. (#1432)

- Added a notification workflow that alerts the support team when an issue is labeled as a Good First Issue Candidate.[(#1296)]
- Added comprehensive training documentation for the `Query` class, covering execution flow, payments, retries, and building child queries. (#1238)
- Beginner issue documentation and updated GFI and GFIC templates and documentation
- Enable auto assignment to good first issues (#1312), archived good first issue support team notification. Changed templates with new assign instruction.
- Intermediate issue documentation
- Added unit test for 'endpoint.py' to increase coverage.
- Automated assignment guard for `advanced` issues; requires completion of at least one `good first issue` and one `intermediate` issue before assignment (exempts maintainers, committers, and triage members). (#1142)
- Added Hbar object support for TransferTransaction HBAR transfers:
- Methods now accept `Union[int, Hbar]` for amount parameters with immediate normalization to tinybars
- Includes comprehensive unit tests covering various Hbar units (HBAR, MICROBAR, NANOBAR, TINYBAR) and accumulation behavior with mixed `int` and `Hbar` inputs
- Added a module-level docstring to the HBAR allowance approval example to clarify delegated spending behavior and key concepts. [#1202](https://github.com/hiero-ledger/hiero-sdk-python/issues/1202)
- Added a GitHub Actions workflow to validate broken Markdown links in pull requests.
- Added method chaining examples to the developer training guide (`docs/sdk_developers/training/coding_token_transactions.md`) (#1194)
- Added documentation explaining how to pin GitHub Actions to specific commit SHAs (`docs/sdk_developers/how-to-pin-github-actions.md`)(#1211)
- examples/mypy.ini for stricter type checking in example scripts
- Formatted examples/tokens directory using black code formatter for consistent code style
- Added `.github/workflows/bot-coderabbit-plan-trigger.yml` to automatically invoke CodeRabbit's plan feature on intermediate and advanced issues, providing implementation guidance to help contributors assess complexity and understand requirements. (#1289)
- Added a GitHub Actions workflow that reminds contributors to link pull requests to issues.
- Added `__str__` and `__repr__` methods to `AccountInfo` class for improved logging and debugging experience (#1098)
- Added Good First Issue (GFI) management and frequency documentation to clarify maintainer expectations and SDK-level GFI governance.
- Added SDK-level Good First Issue (GFI) guidelines for maintainers to clarify what qualifies as a good first issue.
- Codecov workflow
- Added unit tests for `key_format.py` to improve coverage.
- Fix inactivity bot execution for local dry-run testing.
- Added Good First Issue candidate guidelines documentation (`docs/maintainers/good_first_issue_candidate_guidelines.md`) and Good First Issues guidelines documentation (`docs/maintainers/good_first_issues_guidelines.md`) (#1066)
- Added documentation: "Testing GitHub Actions using Forks" (`docs/sdk_developers/training/testing_forks.md`).
- Documentation: created docs/maintainers/hiero_python_sdk_team.md
- Unified the inactivity-unassign bot into a single script with `DRY_RUN` support, and fixed handling of cross-repo PR references for stale detection.
- Added unit tests for `SubscriptionHandle` class covering cancellation state, thread management, and join operations.
- Refactored `account_create_transaction_create_with_alias.py` example by splitting monolithic function into modular functions: `generate_main_and_alias_keys()`, `create_account_with_ecdsa_alias()`, `fetch_account_info()`, `print_account_summary()` (#1016)
- Added `.github/workflows/bot-pr-auto-draft-on-changes.yml` to automatically convert PRs to draft and notify authors when reviewers request changes.
- Add beginner issue template
- Add relevant examples to the beginner issue template
- Add Github CODEOWNERS
- Modularized `transfer_transaction_fungible` example by introducing `account_balance_query()` & `transfer_transaction()`.Renamed `transfer_tokens()` → `main()`
- Phase 2 of the inactivity-unassign bot: Automatically detects stale open pull requests (no commit activity for 21+ days), comments with a helpful InactivityBot message, closes the stale PR, and unassigns the contributor from the linked issue.
- Added `__str__()` to CustomFixedFee and updated examples and tests accordingly.
- Added unit tests for `crypto_utils` (#993)
- Added a github template for good first issues
- Added `.github/workflows/bot-assignment-check.yml` to limit non-maintainers to 2 concurrent issue assignments.
- Configured coderabbit with a `.coderabbit.yaml`
- Added `.github/workflows/bot-community-calls` and its script to notify issue creators of a community call
- Added all missing fields to `__str__()` method and updated `test_tokem_info.py`
- Add examples/tokens/token_create_transaction_pause_key.py example demonstrating token pause/unpause behavior and pause key usage (#833)
- Added `docs/sdk_developers/training/transaction_lifecycle.md` to explain the typical lifecycle of executing a transaction using the Hedera Python SDK.
- Add inactivity bot workflow to unassign stale issue assignees (#952)
- Made custom fraction fee end to end
- feat: AccountCreateTransaction now supports both PrivateKey and PublicKey [#939](https://github.com/hiero-ledger/hiero-sdk-python/issues/939)
- Added Acceptance Criteria section to Good First Issue template for better contributor guidance (#997)
- Added `__str__()` to CustomRoyaltyFee and updated examples and tests accordingly (#986)
- Restore bug and feature request issue templates (#996)(https://github.com/hiero-ledger/hiero-sdk-python/issues/996)
- Support selecting specific node account ID(s) for queries and transactions and added `Network._get_node()` with updated execution flow (#362)
- Add TLS support with two-stage control (`set_transport_security()` and `set_verify_certificates()`) for encrypted connections to Hedera networks. TLS is enabled by default for hosted networks (mainnet, testnet, previewnet) and disabled for local networks (solo, localhost) (#855)
- Add PR inactivity reminder bot for stale pull requests `.github/workflows/pr-inactivity-reminder-bot.yml`
- Add comprehensive training documentation for \_Executable class `docs/sdk_developers/training/executable.md`
- Added empty `docs/maintainers/good_first_issues.md` file for maintainers to write Good First Issue guidelines (#1034)
- Added new `.github/ISSUE_TEMPLATE/04_good_first_issue_candidate.yml` file (1068)(https://github.com/hiero-ledger/hiero-sdk-python/issues/1068)
- Enhanced `.github/ISSUE_TEMPLATE/01_good_first_issue.yml` with welcoming message and acceptance criteria sections to guide contributors in creating quality GFIs (#1052)
- Add workflow to notify team about P0 issues `bot-p0-issues-notify-team.yml`
- Added Issue Reminder (no-PR) bot, .github/scripts/issue_reminder_no_pr.sh and .github/workflows/bot-issue-reminder-no-pr.yml to automatically detect assigned issues with no linked pull requests for 7+ days and post a gentle ReminderBot comment.(#951)
- Add support for include_children in TransactionGetReceiptQuery (#1100)(https://github.com/hiero-ledger/hiero-sdk-python/issues/1100)
- Add new `.github/ISSUE_TEMPLATE/05_intermediate_issue.yml` file (1072)(https://github.com/hiero-ledger/hiero-sdk-python/issues/1072)
- Add a workflow to notify the team when issues are labeled as “good first issues” or identified as candidates for that label: `bot-gfi-notify-team.yml`(#1115)
- Added **str** and **repr** to AccountBalance
- Added GitHub workflow that makes sure newly added test files follow pytest test files naming conventions (#1054)
- Added advanced issue template
- Added advanced issue template for contributors `.github/ISSUE_TEMPLATE/06_advanced_issue.yml`.
- Add new tests to `tests/unit/topic_info_query_test.py` (#1124)
- Added `coding_token_transactions.md` for a high level overview training on how token transactions are created in the python sdk.
- Added prompt for codeRabbit on how to review /examples ([#1180](https://github.com/hiero-ledger/hiero-sdk-python/issues/1180))
- Add Linked Issue Enforcer to automatically close PRs without linked issues `.github/workflows/bot-linked-issue-enforcer.yml`.
- Added support for include duplicates in get transaction receipt query (#1166)
- Added `.github/workflows/cron-check-broken-links.yml` workflow to perform scheduled monthly Markdown link validation across the entire repository with automatic issue creation for broken links ([#1210](https://github.com/hiero-ledger/hiero-sdk-python/issues/1210))
- Added `transfer_transaction_tinybar.py` example demonstrating tinybar transfers with both integer and Hbar object approaches. ([#1249](https://github.com/hiero-ledger/hiero-sdk-python/issues/1249))
- Added `transfer_transaction_gigabar.py` example demonstrating `GIGABAR` unit usage for large-value transfers. ([#1249](https://github.com/hiero-ledger/hiero-sdk-python/issues/1249))
- Coderabbit prompt for .github
- Added convenient factory methods to `Hbar` class for easier instantiation: `from_microbars()`, `from_millibars()`, `from_hbars()`, `from_kilobars()`, `from_megabars()`, and `from_gigabars()`. [#1272](https://github.com/hiero-ledger/hiero-sdk-python/issues/1272)
- Added merge conflict bot workflow (`.github/workflows/bot-merge-conflict.yml`) and helper script (`.github/scripts/bot-merge-conflict.js`) to detect and notify about PR merge conflicts, with retry logic for unknown mergeable states, idempotent commenting, and push-to-main recheck logic (#1247)
- Added workflow to prevent assigning intermediate issues to contributors without prior Good First Issue completion (#1143).
- Added `Client.from_env()` and network-specific factory methods (e.g., `Client.for_testnet()`) to simplify client initialization and reduce boilerplate. [[#1251](https://github.com/hiero-ledger/hiero-sdk-python/issues/1251)]
- Improved unit test coverage for `TransactionId` class, covering parsing logic, hashing, and scheduled transactions.
- Add contract_id support for CryptoGetAccountBalanceQuery([#1293](https://github.com/hiero-ledger/hiero-sdk-python/issues/1293))
- Support for setting `max_query_payment`, `Query.set_max_query_payment()` allows setting a per-query maximum Hbar payment and `Client.set_default_max_query_payment()` sets a client-wide default maximum payment.
- Chained Good First Issue assignment with mentor assignment to bypass GitHub's anti-recursion protection - mentor assignment now occurs immediately after successful user assignment in the same workflow execution. (#1369)
- Add GitHub Actions script and workflow for automatic spam list updates.
- Added technical docstrings and hardening (set -euo pipefail) to the pr-check-test-files.sh script (#1336)
- Added prompt for coderabbit to review `Query` and it's sub-classes.
- Updated the mentor assignment bot welcome message to be more structured. ([#1487](https://github.com/hiero-ledger/hiero-sdk-python/issues/1487))
- Add StakingInfo class ([1364](https://github.com/hiero-ledger/hiero-sdk-python/issues/1364))
- Added a visible confirmation comment when a user unassigns themselves from an issue (#1506)
- Added first-class support for EVM address aliases in `AccountId`, including parsing, serialization, Mirror Node population helpers.
- Add automated bot to recommend next issues to contributors after their first PR merge (#1380)
- Added dry-run support and refactored `.github/workflows/bot-workflows.yml` to use dedicated script `.github/scripts/bot-workflows.js` for improved maintainability and testability. (`#1288`)
- Added MirrorNode based population for `ContractId`, including parsing and serialization support.
- Added `/working` command to reset the inactivity timer on issues and PRs. ([#1552](https://github.com/hiero-ledger/hiero-sdk-python/issues/1552))
- Added `grpc_deadline` support for transaction and query execution.
- Type hints to exception classes (`PrecheckError`, `MaxAttemptsError`, `ReceiptStatusError`) constructors and string methods.

### Documentation
- Added comprehensive docstring to `compress_with_cryptography` function (#1626)
- Replaced the docstring in `entity_id_helper.py` with one that is correct. (#1623)

### Changed
- Refactored AccountInfo class to use the staking_info(#1366)
- chore: format tests/unit/mock_server.py with black (#1542)
- Refactored AccountInfo class to use the staking_info
- Updated actions/checkout to v6.0.1 and actions/github-script v8.0.0 in bot-next-issue-recommendation workflow (#1586)
- Expanded inactivity bot messages to include `/unassign` command information for contributors (#1555)
- Update the acceptance criteria wording in the issue templates to improve clarity and consistency for contributors (#1491)
- Add return type hint to `AccountId.__repr__` for type consistency. (#1503)
- Good First Issue template to have more guidance and renamed other templates for consistency with upstream
- Added AI usage guidelines to the Good First Issue and Beginner issue templates to guide contributors on responsible AI use. (#1490)
- Refactored `bot-verified-commits.yml` workflow to use modular JavaScript with configurable environment variables, input sanitization, dry-run mode support, and SHA-pinned actions. (#1482)
- Refactored the advanced issue assignment guard to use a single configurable variable for the required number of completed intermediate issues. (#1479)
- Align Good First Issue and Good First Issue — Candidate guidelines with the Hiero C++ SDK for clarity and consistency.(#1421)
- Make the required signed commit command explicit in all issue templates to reduce PR signing errors for contributors (#1489)
- Refactored `file_info_query.py` to use `print(info)` instead of manual formatting (#1451)
- Enable CodeRabbit walkthrough mode by default to improve PR review visibility (#1439)
- Move assignment guards to be directly inside the gfi and beginner auto assign
- Remove the commented out blocks in config.yml (#1435)
- Renamed `.github/scripts/check_advanced_requirement.sh` to `bot-advanced-check.sh` for workflow consistency (#1341)
- Difficulty guidelines to feel more welcoming
- Added global review instructions to CodeRabbit configuration to limit reviews to issue/PR scope and prevent scope creep [#1373]
- Archived unused auto draft GitHub workflow to prevent it from running (#1371)
- Added comprehensive documentation to the PR changelog check script (`.github/scripts/pr-check-changelog.sh`) to clarify behavior, inputs, permissions, and dependencies [(#1337)]
- Refactored `account_create_transaction_without_alias.py` into smaller, modular functions.(#1321)
- Renamed bot-inactivity workflow files to remove "-phase" suffix since the process no longer uses phased execution (#1339)
- Renamed the GitHub notify team script to match its corresponding workflow filename for better maintainability (#1338)
- style: apply black formatting to examples (#1299)
- Update GitHub workflow names in `.github/workflows/bot-workflows.yml` to match correct references [(#1284)]
- Updated set up and workflow documents for improved clarity and organisation
- Renamed templates for improved clarity [(#1265)]
- Updated Good First Issue notifications to trigger only after the first comment is posted, reducing noise on unassigned issues.(#1212)
- Bumped requests from 2.32.3 to 2.32.4 to 2.32.5
- Moved `docs/sdk_developers/how_to_link_issues.md` to `docs/sdk_developers/training/workflow/how_to_link_issues.md` and updated all references (#1222)
- Moved docs/sdk_developers/project_structure.md to docs/sdk_developers/training/setup/project_structure.md and ensured all previous references are updated [#1223](https://github.com/hiero-ledger/hiero-sdk-python/issues/1223)
- Renamed workflow scripts in `.github/scripts/` to match their corresponding workflow file names for improved consistency and maintainability (#1198)
- Refactored `account_create_transaction_evm_alias.py` to improve readability by splitting the monolithic function into smaller helper functions. [#1017](https://github.com/hiero-ledger/hiero-sdk-python/issues/1017)
- Improved docstring for `account_allowance_approve_transaction_nft.py` with purpose, key concepts and required vs optional steps.
- Updated Codecov coverage thresholds in 'codecov.yml' to require 90% of project coverage and 92% of patch coverage (#1157)
- Reduce office-hours reminder spam by posting only on each user's most recent open PR, grouping by author and sorting by creation time (#1121)
- Reduce office-hours reminder spam by never posting on PRs of maintainers and committers
- Pylint cleanup for token_airdrop_transaction_cancel.py (#1081) [@tiya-15](https://github.com/tiya-15)
- Move `account_allowance_delete_transaction_hbar.py` from `examples/` to `examples/account/` for better organization (#1003)
- Improved consistency of transaction examples (#1120)
- Refactored `account_create_transaction_with_fallback_alias.py` by splitting the monolithic `create_account_with_fallback_alias` function into modular functions: `generate_fallback_key`, `fetch_account_info`, and `print_account_summary`. The existing `setup_client()` function was reused for improved readability and structure (#1018)
- Allow `PublicKey` for batch_key in `Transaction`, enabling both `PrivateKey` and `PublicKey` for batched transactions
- Allow `PublicKey` for `TokenUpdateKeys` in `TokenUpdateTransaction`, enabling non-custodial workflows where operators can build transactions using only public keys (#934).
- Bump protobuf toml to protobuf==6.33.2
- Improved the contributing section for sdk developers in CONTRIBUTING.md for clarity and including new documentation
- chore: Move account allowance example to correct folder
- Added more tests to the CustomFee class for different functionalities (#991)
- Changed messaged for test failure summaries so it is clearer by extracting test failure names into summary
- Renamed example files to match src naming (#1053)
- Updated bot naming conventions in `.github/workflows` to be consistent (#1042)
- Renamed workflow files for consistent PR check naming:
  `examples.yml` → `pr-check-examples.yml`,
  `test.yml` → `pr-check-test.yml` (#1043)
- Cleaned up `token_airdrop_claim_auto` example for pylint compliance (no functional changes). (#1079)
- Formatted `examples/query` using black (#1082)(https://github.com/hiero-ledger/hiero-sdk-python/issues/1082)
- Update team notification script and workflow for P0 issues 'p0_issues_notify_team.js'
- Rename test files across the repository to ensure they consistently end with \_test.py (#1055)
- Cleaned up `token_airdrop_claim_signature_required` example for pylint compliance (no functional changes). (#1080)
- Rename the file 'test_token_fee_schedule_update_transaction_e2e.py' to make it ends with \_test.py as all other test files.(#1117)
- Format token examples with Black for consistent code style and improved readability (#1119)
- Transformed `examples/tokens/custom_fee_fixed.py` to be an end-to-end example, that interacts with the Hedera network, rather than a static object demo.
- Format token examples with Black for consistent code style and improved readability (#1119)
- Replaced `ResponseCode.get_name(receipt.status)` with the `ResponseCode(receipt.status).name` across examples and integration tests for consistency. (#1136)
- Moved helpful references to Additional Context section and added clickable links.
- Transformed `examples\tokens\custom_royalty_fee.py` to be an end-to-end example, that interacts with the Hedera network, rather than a static object demo.
- Refactored `examples/tokens/custom_royalty_fee.py` by splitting monolithic function custom_royalty_fee_example() into modular functions create_royalty_fee_object(), create_token_with_fee(), verify_token_fee(), and main() to improve readability, cleaned up setup_client() (#1169)
- Added comprehensive unit tests for Timestamp class (#1158)
- Enhance unit and integration test review instructions for clarity and coverage `.coderabbit.yaml`.
- Issue reminder bot now explicitly mentions assignees (e.g., `@user`) in comments. ([#1232](https://github.com/hiero-ledger/hiero-sdk-python/issues/1232))
- Updated `transfer_transaction_hbar.py` example to use `Hbar` objects instead of raw integers and added receipt checking with `ResponseCode` validation.([#1249](https://github.com/hiero-ledger/hiero-sdk-python/issues/1249))
- Renamed `pr-missing-linked-issue.yml` and `pr_missing_linked_issue.js` to `bot-pr-missing-linked-issue.yml` and `bot-pr-missing-linked-issue.js` respectively. Enhanced LinkBot PR comment with clickable hyperlinks to documentation for linking issues and creating issues. (#1264)
- Enhance assignment bot to guard against users with spam PRs `.github/scripts/bot-assignment-check.sh`
- Add CodeRabbit documentation review prompts for docs, sdk_users, and sdk_developers with priorities, philosophy, and edge case checks. ([#1236](https://github.com/hiero-ledger/hiero-sdk-python/issues/1236))
- Enhance NodeAddress tests with additional coverage for proto conversion `tests/unit/node_address_test.py`
- Replaced deprecated `AccountCreateTransaction.set_key()` usage with `set_key_without_alias()` and `set_key_with_alias()` across examples and tests

- Updated `pyproject.toml` to enforce stricter Ruff linting rules, including Google-style docstrings (`D`), import sorting (`I`), and modern Python syntax (`UP`).
- Modified and renamed hasIntermediateOrAdvancedLabel() to check if issue label is beginner or higher (#1385)
- Updated `.github/scripts/bot-office-hours.sh` to detect and skip PRs created by bot accounts when posting office hours reminders. (#1384)
- Refactored `examples/account/account_create_transaction_create_with_alias.py` and `examples/account/account_create_transaction_evm_alias.py` to use the native `AccountInfo.__str__` method for printing account details, replacing manual JSON serialization. ([#1263](https://github.com/hiero-ledger/hiero-sdk-python/issues/1263))
- Enhance TopicInfo `__str__` method and tests with additional coverage, and update the format_key function in `key_format.py` to handle objects with a \_to_proto method.
- Update changelog workflow to trigger automatically on pull requests instead of manual dispatch (#1567)
- Formatted key-related unit test files (`key_utils_test.py`, `test_key_format.py`, `test_key_list.py`) using the black formatter
- Add return type hint to `ContractId.__str__`. (#1654)

- chore: update maintainer guidelines link in MAINTAINERS.md (#1605)
- chore: update merge conflict bot message with web editor tips (#1592)
- chore: update MAINTAINERS.md to include new maintainer Manish Dait and sort maintainers by GitHub ID. (#1691)

### Fixed
- Updated Good First Issue recommendations to supported Hiero repositories. (#1689)
- Fix the next-issue recommendation bot to post the correct issue recommendation comment. (#1593)
- Ensured that the GFI assignment bot skips posting `/assign` reminders for repository collaborators to avoid unnecessary notifications.(#1568).
- Reduced notification spam by skipping the entire advanced qualification job for non-advanced issues and irrelevant events (#1517)
- Aligned token freeze example filename references and improved error handling by catching broader exceptions with clearer messages. (#1412)
- Fixed jq syntax in bot-office-hours.sh (#1502)
- Fixed formatting of `/unassign` command in the PR inactivity reminder message so it displays correctly with backticks. (#1582)
- Prevented linkbot from commenting on or auto-closing bot-authored pull requests. (#1516)
- Respect `dry-run` input in `bot-community-calls.yml` workflow (#1425)
- Updated LinkBot regex in the GitHub Actions bot script to support "Closes" and "Resolves" keywords for improved PR body-link detection (#1465)
- Fixed CodeRabbit plan trigger workflow running multiple times when issues are created with multiple labels by switching to labeled event trigger only. (#1427)
- Prevent LinkBot from posting duplicate “missing linked issue” comments on pull requests. (#1475)
- Refined intermediate assignment guard to validate Beginner issue completion with improved logging and GraphQL-based counting. (#1424)
- Improved filename-related error handling with clearer and more descriptive error messages.(#1413)
- Good First Issue bot no longer posts `/assign` reminders for repository collaborators. (#1367)
- GFI workflow casing
- Update `bot-workflows.yml` to trigger only on open PRs with failed workflows; ignore closed PRs and branches without open PRs.
- Fixed step-security/harden-runner action SHA in merge conflict bot workflow (#1278)
- Fixed the README account balance example to use correct SDK APIs and provide a runnable testnet setup. (#1250)
- Fix token association verification in `token_airdrop_transaction.py` to correctly check if tokens are associated by using `token_id in token_balances` instead of incorrectly displaying zero balances which was misleading (#[815])
- Fixed inactivity bot workflow not checking out repository before running (#964)
- Fixed the topic_message_query integarion test
- good first issue template yaml rendering
- Fixed solo workflow defaulting to zero
- Fix unit test tet_query.py
- TLS Hostname Mismatch & Certificate Verification Failure for Nodes
- Workflow does not contain permissions for `pr-check-test-files` and `pr-check-codecov`
- Fixed `cron-check-broken-links.yml` string parsing issue in context input `dry_run` (#1235)
- Flaky tests by disabling TLS in mock Hedera nodes in `mock_server.py`
- Fixed LinkBot permission issue for fork PRs by changing trigger to pull_request_target and adding proper permissions.
- Fixed token examples to consistently use setup_client without tuple unpacking.(#1397)
- Fixed duplicate comment prevention in issue reminder bot by adding hidden HTML marker for reliable comment detection (.github/scripts/bot-issue-reminder-no-pr.sh) (#1372)
- Fixed bot-pr-missing-linked-issue to skip commenting on pull requests created by automated bots. (#1382)
- Updated `.github/scripts/bot-community-calls.sh` to skip posting reminders on issues created by bot accounts. (#1383)
- Fixed incorrect run instructions and broaden error handling in `token_dissociate_transaction.py` example to improve usability for new users (#1468)
- Update `.github/scripts/bot-advanced-check.sh` to unassign unqualified users.
- Fixed broken project structure link in `CONTRIBUTING.md` (#1664)

### Removed

- Deleted `examples/utils.py` as its helper functions are no longer needed. ([#1263](https://github.com/hiero-ledger/hiero-sdk-python/issues/1263))

### Breaking Change

- Remove deprecated 'in_tinybars' parameter and update related tests `/src/hiero_sdk_python/hbar.py`, `/tests/unit/hbar_test.py` and `/src/hiero_sdk_python/tokens/custom_fixed_fee.py`.

## [0.1.10] - 2025-12-03

### Added

- Added docs/sdk_developers/training/workflow: a training for developers to learn the workflow to contribute to the python SDK.
- Added Improved NFT allowance deletion flow with receipt-based status checks and strict `SPENDER_DOES_NOT_HAVE_ALLOWANCE` verification.
- Add `max_automatic_token_associations`, `staked_account_id`, `staked_node_id` and `decline_staking_reward` fields to `AccountUpdateTransaction` (#801)
- Added docs/sdk_developers/training/setup: a training to set up as a developer to the python sdk
- Add example demonstrating usage of `CustomFeeLimit` in `examples/transaction/custom_fee_limit.py`
- Added `.github/workflows/merge-conflict-bot.yml` to automatically detect and notify users of merge conflicts in Pull Requests.
- Added `.github/workflows/bot-office-hours.yml` to automate the Weekly Office Hour Reminder.
- feat: Implement account creation with EVM-style alias transaction example.
- Added validation logic in `.github/workflows/pr-checks.yml` to detect when no new chnagelog entries are added under [Unreleased].
- Support for message chunking in `TopicSubmitMessageTransaction`.

### Changed

- bot workflows to include new changelog entry
- Removed duplicate import of transaction_pb2 in transaction.py
- Refactor `TokenInfo` into an immutable dataclass, remove all setters, and rewrite `_from_proto` as a pure factory for consistent parsing [#800]
- feat: Add string representation method for `CustomFractionalFee` class and update `custom_fractional_fee.py` example.
- Moved query examples to their respective domain folders to improve structure matching.

### Fixed

- fixed workflow: changelog check with improved sensitivity to deletions, additions, new releases

## [0.1.9] - 2025-11-26

### Added

- Add a limit of one comment for PR to the commit verification bot. [#892]
- Removed `actions/checkout@v4` from `bot-verified-commits.yml`
- Add comprehensive documentation for `ReceiptStatusError` in `docs/sdk_developers/training/receipt_status_error.md`
- Add practical example `examples/errors/receipt_status_error.py` demonstrating transaction error handling
- Document error handling patterns and best practices for transaction receipts
- fix `pull_request` to `pull_request_target` in `bot-verified-commits.yml`
- Add more robust receipt checks and removed fallback to `examples/tokens/token_delete_transaction.py`
- Add detail to `token_airdrop.py` and `token_airdrop_cancel.py`
- Add workflow: github bot to respond to unverified PR commits (#750)
- Add workflow: bot workflow which notifies developers of workflow failures in their pull requests.
- Add `examples/token_create_transaction_max_automatic_token_associations_0.py` to demonstrate how `max_automatic_token_associations=0` behaves.
- Add `examples/topic_id.py` to demonstrate `TopicId` opeartions
- Add `examples/topic_message.py` to demonstrate `TopicMessage` and `TopicMessageChunk` with local mock data.
- Added missing validation logic `fee_schedule_key` in integration `token_create_transaction_e2e_test.py` and ``token_update_transaction_e2e_test.py`.
- Add `account_balance_query.py` example to demonstrate how to use the CryptoGetAccountBalanceQuery class.
- Add `examples/token_create_transaction_admin_key.py` demonstrating admin key privileges for token management including token updates, key changes, and deletion (#798)
- Add `examples/token_create_transaction_freeze_key.py` showcasing freeze key behavior, expected failures without the key, and the effect of freezing/unfreezing on transfers.
- Add `examples/account_info.py` to demonstrate `AccountInfo` opeartions
- Added `HbarUnit` class and Extend `Hbar` class to handle floating-point numbers
- Add `examples/topic_info.py` to demonstrate `TopicInfo` operations.
- feat: Allow `PrivateKey` to be used for keys in `TopicCreateTransaction` for consistency.
- EvmAddress class
- `alias`, `staked_account_id`, `staked_node_id` and `decline_staking_reward` fields to AccountCreateTransaction
- `staked_account_id`, `staked_node_id` and `decline_staking_reward` fields to AccountInfo
- Added `examples/token_create_transaction_supply_key.py` to demonstrate token creation with and without a supply key.
- Added `examples/token_create_transaction_kyc_key.py` to demonstrate KYC key functionality, including creating tokens with/without KYC keys, granting/revoking KYC status, and understanding KYC requirements for token transfers.
- Add `set_token_ids`, `_from_proto`, `_validate_checksum` to TokenAssociateTransaction [#795]
- Added BatchTransaction class
- Add support for token metadata (bytes, max 100 bytes) in `TokenCreateTransaction`, including a new `set_metadata` setter, example, and tests. [#799]
- Added `examples/token_create_transaction_token_fee_schedule.py` to demonstrate creating tokens with custom fee schedules and the consequences of not having it.
- Added `examples/token_create_transaction_wipe_key.py` to demonstrate token wiping and the role of the wipe key.
- Added `examples/account_allowance_approve_transaction_hbar.py` and `examples/account_allowance_delete_transaction_hbar.py`, deleted `examples/account_allowance_hbar.py`. [#775]
- Added `docs\sdk_developers\training\receipts.md` as a training guide for users to understand hedera receipts.
- Add `set_token_ids`, `_from_proto`, `_validate_checksum` to TokenAssociateTransaction [#795]
- docs: added `network_and_client.md` with a table of contents, and added external example scripts (`client.py`).

### Changed

- Upgraded step-security/harden-runner v2.13.2
- bumped actions/checkout from 5.0.0 to 6.0.0
- Limit workflow bot to one message per PR
- Refactored token-related example scripts (`token_delete.py`, `token_dissociate.py`, etc.) for improved readability and modularity. [#370]
- upgrade: step security action upgraded from harden-runner-2.13.1 to harden-runner-2.13.1
- chore: Split `examples/account_allowance_nft.py` into separate `account_allowance_approve_transaction_nft.py` and `account_allowance_delete_transaction_nft.py` examples.
- chore: bump protobuf from 6.33.0 to 6.33.1 (#796)
- fix: Allow `max_automatic_token_associations` to be set to -1 (unlimited) in `AccountCreateTransaction` and add field to `AccountInfo`.
- Allow `PrivateKey` to be used for keys in `TopicCreateTransaction` for consistency.
- Update github actions checkout from 5.0.0 to 5.0.1 (#814)
- changed to add concurrency to workflow bot
- feat: Refactor `TokenDissociateTransaction` to use set_token_ids method and update transaction fee to Hbar, also update `transaction.py` and expand `examples/token_dissociate.py`, `tests/unit/token_dissociate.py`.

### Fixed

- chore: updated solo action to avoid v5
- chore: fix test.yml workflow to log import errors (#740)
- chore: fixed integration test names without a test prefix or postfix
- Staked node ID id issue in the account_create_transationt_e2e_test
- workflow: verified commits syntax for verfication bot

## [0.1.8] - 2025-11-07

### Added

- `is_unknown` property added to `src/hiero_sdk_python/response_code.py`
- Example `response_code.py`
- Add `TokenFeeScheduleUpdateTransaction` class to support updating custom fee schedules on tokens (#471).
- Add `examples/token_update_fee_schedule_fungible.py` and `examples/token_update_fee_schedule_nft.py` demonstrating the use of `TokenFeeScheduleUpdateTransaction`.
- Update `docs/sdk_users/running_examples.md` to include `TokenFeeScheduleUpdateTransaction`.
- added FreezeTransaction class
- added FreezeType class
- Added `docs/sdk_developers/pylance.md`, a new guide explaining how to set up and use **Pylance** in VS Code for validating imports, file references, and methods before review. (#713)
- feat: TokenAirdropClaim Transaction, examples (with signing required and not), unit and integration tests (#201)
- docs: Add Google-style docstrings to `TokenId` class and its methods in `token_id.py`.
- added Google-style docstrings to the `TransactionRecord` class including all dataclass fields, `__repr__`, `_from_proto()` & `_to_proto()` methods.
- Standardized docstrings, improved error handling, and updated type hinting (`str | None` to `Optional[str]`) for the `FileId` class (#652).
- Add Google-style docstrings to `AccountInfo` class and its methods in `account_info.py`.
- Added comprehensive Google-style docstrings to the `Logger` class and all utility functions in `src/hiero_sdk_python/logger/logger.py` (#639).
- add AccountRecordsQuery class
- chore: added python 3.13 to test.yml workflow (#510, #449)
- Transaction bytes serialization support: `Transaction.freeze()`, `Transaction.to_bytes()`, and `Transaction.from_bytes()` methods for offline signing and transaction storage
- docs: Add Google-style docstrings to `ContractId` class and methods in `contract_id.py`.
- Added TokenUnpauseTransaction class
- Added expiration_time, auto_renew_period, auto_renew_account, fee_schedule_key, kyc_key in `TokenCreateTransaction`, `TokenUpdateTransaction` classes
- Added comprehensive Google-style docstrings to the `CustomFee` class and its methods in `custom_fee.py`.
- docs: Add `docs/sdk_developers/project_structure.md` to explain repository layout and import paths.

### Changed
- chore: renamed examples to match src where possible
- Moved examples/ to be inside subfiles to match src structure
- changed example script workflow to run on new subdirectory structure
- chore: bumped solo action from 14.0 to 15.0 (#764)
- chore: replaced hardcoded 'testnet' messages with environment network name
- chore: validate that token airdrop transactions require an available token service on the channel (#632)
- chore: update local environment configuration in env.example (#649)
- chore: Update env.example NETWORK to encourage testnet or local usage (#659)
- chore: updated pyproject.toml with python 3.10 to 3.13 (#510, #449)
- chore: fix type hint for TokenCancelAirdropTransaction pending_airdrops parameter
- chore: Moved documentation file `common_issues.md` from `examples/sdk_developers/` to `docs/sdk_developers/` for unified documentation management (#516).
- chore: Refactored the script of examples/custom_fee.py into modular functions
- fix: Replaced `collections.namedtuple` with `typing.NamedTuple` in `client.py` for improved type checking.
- chore: Refactored examples/custom_fee.py into three separate example files.
- Expanded `docs/sdk_developers/checklist.md` with a self-review guide for all pull request submission requirements (#645).
- Expanded docs/sdk_developers/signing.md to clarify GPG and DCO requirements and add a Table of Contents (#455).
- chore: Standardized client initialization across all examples/ files to promote consistency (#658).
- chore: changed the file names of airdrop examples, classes, unit and integration tests so they are grouped together. (#631)
- Refactor `AbstractTokenTransferTransaction` to unify Token/NFT transfer logic.

### Fixed

- Added explicit read permissions to examples.yml (#623)
- Removed deprecated Logger.warn() method and legacy parameter swap logic from get_logger() (#673).
- Improved type hinting in `file_append_transaction.py` to resolve 'mypy --strict` errors. ([#495](https://github.com/hiero-ledger/hiero-sdk-python/issues/495))
- fix: Resolve `__eq__` type conflict in `CustomFee` class (#627)
- Fixes a type conflict in `token_id.py` where `from_string` could receive `None`, preventing a runtime error by raising a `ValueError` if the input is missing. #630
- Dependabot alerts (version bumps)
- Fixed incorrect `TokenType` import (protobuf vs. SDK enum) in 18 example files.
- Update `schedule_sign_transaction_e2e_test` to check for key presence instead of relying on index.
- Add `localhost` and `local` as network names

### Breaking Changes

- chore: changed the file names airdrop classes (#631)
  {pending_airdrop_id.py -> token_airdrop_pending_id.py}
  {pending_airdrop_record.py -> token_airdrop_pending_record.py}
  {token_cancel_airdrop_transaction.py -> token_airdrop_transaction_cancel.py}

- In `TokenAirdropTransaction` the parameters of the following methods have been renamed:
  - add_nft_transfer(sender → sender_id, receiver → receiver_id)
  - add_approved_nft_transfer(sender → sender_id, receiver → receiver_id)

## [0.1.7] - 2025-10-28

### Added

- Expanded `README.md` with a new "Follow Us" section detailing how to watch, star, and fork the repository (#472).
- Refactored `examples/topic_create.py` into modular functions for better readability and reuse.
- Add Rebasing and Signing section to signing.md with instructions for maintaining commit verification during rebase operations (#556)
- Add `examples/account_id.py` demonstrating AccountId class usage including creating standard AccountIds, parsing from strings, comparing instances, and creating AccountIds with public key aliases
- Added Google-style docstrings to `CustomFractionalFee` class and its methods in `custom_fractional_fee.py`.
- Added `dependabot.yaml` file to enable automated dependency management.
- Common issues guide for SDK developers at `examples/sdk_developers/common_issues.md`
- Added documentation for resolving changelog conflicts in `docs/common_issues.md`
- Added comprehensive changelog entry guide at `docs/sdk_developers/changelog.md` to help contributors create proper changelog entries (#532).
- docs: Added Google-style docstrings to `CustomFixedFee` class and its methods in `custom_fixed_fee.py`.
- docs: Add Google-style docstrings to `CustomRoyaltyFee` class and its methods in `custom_royalty_fee.py`.
- docs: Add Google-style docstrings to `AbstractTokenTransferTransaction` class and its methods in `abstract_token_transfer_transaction.py`.
- docs: Add Google-style docstrings to `TokenRelationship` class and its methods in `token_relationship.py`.
- feat: add initial testing guide structure
- Added `checksum` filed for TopicId, FileId, ContractId, ScheduleId class
- Added workflow for running example scripts.
- docs: workflow.md documenting key steps to creating a pull request (#605)
- chore: fix the examples workflow to log error messages and run on import failure (#738)
- Added `docs/discord.md` explaining how to join and navigate the Hiero community Discord (#614).

### Changed

- Added direct links to Python SDK channel in Linux Foundation Decentralized Trust Discord back in
- Updated all occurrences of non-functional Discord invite links throughout the documentation with the new, stable Hyperledger and Hedera invite links (#603).
- Refactored TopicId class to use @dataclass decorator for reducing boilerplate code
- Renamed `examples/nft_allowance.py` to `examples/account_allowance_nft.py` for consistency with account class naming scheme
- Added changelog conflict resolution examples to `docs/common_issues.md`
- Refactored `examples/topic_create.py` to be more modular by splitting functions and renaming `create_topic()` to `main()`.
- Refactored `examples/transfer_hbar.py` to improve modularity by separating transfer and balance query operations into dedicated functions
- Enhanced contributing section in README.md with resource links
- Refactored examples/topic_message_submit.py to be more modular
- Added "One Issue Per Pull Request" section to `examples/sdk_developers/common_issues.md`.
- docs: Improved the contributing section in the README.md file
- Refactored `examples/transfer_nft.py` to be more modular by isolating transfer logic.
- Refactored `examples/file_append.py` into modular functions for better readability, reuse, and consistency across examples.
- Ensured identical runtime behavior and output to the previous version to maintain backward compatibility.
- Renamed `examples/hbar_allowance.py` to `examples/account_allowance_hbar.py` for naming consistency
- Converted monolithic function in `token_create_nft_infinite.py` to multiple modular functions for better structure and ease.
- docs: Use relative paths for internal GitHub links (#560).
- Update pyproject.toml maintainers list.
  – docs: Updated README.md/CHANGELOG.md and added blog.md, bud.md and setup.md (#474)
- renamed docs/sdk_developers/changelog.md to docs/sdk_developers/changelog_entry.md for clarity.
- Refactor `query_balance.py` into modular, reusable functions with `setup_client()`, `create_account()`, `get_balance()`, `transfer_hbars()`, and `main()` for improved readability, maintainability, and error handling.
- Unified balance and transfer logging format — both now consistently display values in hbars for clarity.

### Fixed

- Add type hints to `setup_client()` and `create_new_account()` functions in `examples/account_create.py` (#418)
- Added explicit read and write permissions to test.yml
- Type hinting for `Topic` related transactions.

### Removed

- Remove deprecated camelCase alias support and `_DeprecatedAliasesMixin`; SDK now only exposes snake_case attributes for `NftId`, `TokenInfo`, and `TransactionReceipt`. (Issue #428)

## [0.1.6] - 2025-10-21

### Added

- Add comprehensive Google-style docstrings to examples/account_create.py
- add revenue generating topic tests/example
- add fee_schedule_key, fee_exempt_keys, custom_fees fields in TopicCreateTransaction, TopicUpdateTransaction, TopicInfo classes
- add CustomFeeLimit class
- TokenNftAllowance class
- TokenAllowance class
- HbarAllowance class
- HbarTransfer class
- AccountAllowanceApproveTransaction class
- AccountAllowanceDeleteTransaction class
- FileAppendTransaction class
- Documentation examples for Allowance Approve Transaction, Allowance Delete Transaction, and File Append Transaction
- Approved transfer support to TransferTransaction
- set_transaction_id() API to Transaction class
- Allowance examples (hbar_allowance.py, token_allowance.py, nft_allowance.py)
- Refactored examples/logging_example.py for better modularity (#478)

### Changed

- TransferTransaction refactored to use TokenTransfer and HbarTransfer classes instead of dictionaries
- Added checksum validation for TokenId
- Refactor examples/token_cancel_airdrop
- Refactor token creation examples for modularity and consistency
- Updated `signing.md` to clarify commit signing requirements, including DCO, GPG, and branch-specific guidelines (#459)

### Changed

- Rearranged running_examples.md to be alphabetical
- Refactor token_associate.py for better structure, add association verification query (#367)
- Refactored `examples/account_create.py` to improve modularity and readability (#363)
- Replace Hendrik Ebbers with Sophie Bulloch in the MAINTAINERS.md file
- Improved `CONTRIBUTING.md` by explaining the /docs folder structure and fixing broken hyperlinks.(#431)
- Converted class in `token_nft_info.py` to dataclass for simplicity.

### Fixed

- Incompatible Types assignment in token_transfer_list.py
- Corrected references to \_require_not_frozen() and removed the surplus \_is_frozen
- Removed duplicate static methods in `TokenInfo` class:
    - `_copy_msg_to_proto`
    - `_copy_key_if_present`
    - `_parse_custom_fees`
    Kept robust versions with proper docstrings and error handling.
- Add strict type hints to `TransactionGetReceiptQuery` (#420)
- Fixed broken documentation links in CONTRIBUTING.md by converting absolute GitHub URLs to relative paths
- Updated all documentation references to use local paths instead of pointing to hiero-sdk project hub

## [0.1.5] - 2025-09-25

### Added

- ScheduleSignTransaction class
- NodeUpdateTransaction class
- NodeDeleteTransaction class
- ScheduleDeleteTransaction class
- prng_number and prng_bytes properties in TransactionRecord
- PrngTransaction class
- ScheduleInfoQuery class
- ScheduleInfo class
- Exposed node_id property in `TransactionReceipt`
- NodeCreateTransaction class
- ScheduleId() class
- ScheduleCreateTransaction() class
- build_scheduled_body() in every transaction
- ContractDeleteTransaction class
- ContractExecuteTransaction class
- setMessageAndPay() function in StatefulContract
- AccountDeleteTransaction Class
- generate_proto.py
- Bumped Hedera proto version from v0.57.3 to v0.64.3
- Added `dev` and `lint` dependency groups as default in `pyproject.toml`
- EthereumTransaction class
- AccountId support for ECDSA alias accounts
- ContractId.to_evm_address() method for EVM compatibility
- consumeLargeData() function in StatefulContract
- example script for Token Airdrop
- added variables directly in the example script to reduce the need for users to supply extra environment variables.
- Added new `merge_conflicts.md` with detailed guidance on handling conflicts during rebase.
- Type hinting to /tokens, /transaction, /query, /consensus
- Linting to /tokens, /transaction, /query, /consensus
- Module docstrings in /tokens, /transaction, /query, /consensus
- Function docstrings in /tokens, /transaction, /query, /consensus

### Changed

- bump solo version to `v0.14`
- bump protobufs version to `v0.66.0`
- bump solo version to `v0.13`
- Extract \_build_proto_body() from build_transaction_body() in every transaction
- StatefulContract's setMessage() function designed with no access restrictions, allowing calls from any address
- bump solo version to `v0.12`
- Extract Ed25519 byte loading logic into private helper method `_from_bytes_ed25519()`
- Documentation structure updated: contents moved from `/documentation` to `/docs`.
- Switched Mirror Node endpoints used by SDK to secure ones instead of deprecated insecure endpoints (shut down on Aug 20th, see [Hedera blogpost](https://hedera.com/blog/updated-deprecation-of-the-insecure-hedera-consensus-service-hcs-mirror-node-endpoints))
- Update protobuf dependency from 5.28.1 to 5.29.1
- Update grpcio dependency from 1.68.1 to 1.71.2
- Updated `rebasing.md` with clarification on using `git reset --soft HEAD~<n>` where `<n>` specifies the number of commits to rewind.
- Calls in examples for PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY')) to PrivateKey.from_string(os.getenv('OPERATOR_KEY')) to enable general key types
- Add CI tests across Python 3.10–3.12.
- kyc_status: Optional[TokenFreezeStatusProto] = None → kyc_status: Optional[TokenKycStatus] = None
- assert relationship.freeze_status == TokenFreezeStatus.FROZEN, f"Expected freeze status to be FROZEN, but got {relationship.freeze_status}" → assert relationship.freeze_status == TokenFreezeStatus.UNFROZEN, f"Expected freeze status to be UNFROZEN, but got {relationship.freeze_status}"

### Fixed

- Format account_create_transaction.py and add type hints
- Format account_balance.py and fix pylint issues
- Format account_delete_transaction.py and fix pylint issues
- Format account_id.py and fix pylint issues
- Format account_info.py and fix pylint issues
- Format account_update_transaction.py and fix pylint issues
- Unit test compatibility issues when running with UV package manager
- Type annotations in TokenRelationship class (kyc_status and freeze_status)
- Test assertions in test_executable.py using pytest match parameter
- Moved and renamed README_upstream.md to docs/sdk_developers/rebasing.md
- Invalid DRE Hex representation in examples/keys_private_ecdsa.py
- Windows malformed path using uv run generate_proto.py using as_posix()
- Changed README MIT license to Apache
- deprecated CamelCase instances in /examples such as TokenId and totalSupply to snake_case
- Invalid HEX representation and signature validation in keys_public_ecdsa.py
- Invalid signature verification for examples/keys_public_der.py
- Duplicate validation function in TokenCreate

### Removed

- Removed the old `/documentation` folder.
- Rebase command in README_upstream changed to just -S
- generate_proto.sh
- pkg_resources dependency in generate_proto.py

### Breaking API changes

- We have some changed imports and returns to maintain compatability in the proto bump

transaction_body_pb2.TransactionBody -> transaction_pb2.TransactionBody
contract_call_local_pb2.ContractFunctionResult -> contract_types_pb2.ContractFunctionResult
contract_call_local_pb2.ContractLoginfo -> contract_types_pb2.ContractLoginfo

- Removed init.py content in /tokens

**Changed imports**

- src/hiero_sdk_python/consensus/topic_message.py: from hiero_sdk_python import Timestamp → from hiero_sdk_python.timestamp import Timestamp
- src/hiero_sdk_python/query/topic_message_query.py: from hiero_sdk_python import Client → from hiero_sdk_python.client.client import Client
- src/hiero_sdk_python/tokens/**init**.py: content removed.
- src/hiero_sdk_python/tokens/token_info.py: from hiero_sdk_python.hapi.services.token_get_info_pb2 import TokenInfo as proto_TokenInfo → from hiero_sdk_python.hapi.services import token_get_info_pb2
- src/hiero_sdk_python/tokens/token_key_validation.py: from hiero_sdk_python.hapi.services → import basic_types_pb2
- src/hiero_sdk_python/tokens/token_kyc_status.py: from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenKycStatus as proto_TokenKycStatus → from hiero_sdk_python.hapi.services import basic_types_pb2
- src/hiero_sdk_python/tokens/token_pause_status.py: from hiero_sdk_python.hapi.services.basic_types_pb2 import (TokenPauseStatus as proto_TokenPauseStatus,) → from hiero_sdk_python.hapi.services import basic_types_pb2
- src/hiero_sdk_python/tokens/token_pause_transaction.py: from hiero_sdk_python.hapi.services.token_pause_pb2 import TokenPauseTransactionBody → from hiero_sdk_python.hapi.services import token_pause_pb2, transaction_pb2
- from hiero_sdk_python.hapi.services.token_revoke_kyc_pb2 import TokenRevokeKycTransactionBody → from hiero_sdk_python.hapi.services import token_revoke_kyc_pb2, transaction_pb2
- src/hiero_sdk_python/tokens/token_update_nfts_transaction.py: from hiero_sdk_python.hapi.services.token_update_nfts_pb2 import TokenUpdateNftsTransactionBody → from hiero_sdk_python.hapi.services import token_update_nfts_pb2,transaction_pb2
- src/hiero_sdk_python/tokens/token_wipe_transaction.py: from hiero_sdk_python.hapi.services.token_wipe_account_pb2 import TokenWipeAccountTransactionBody → from hiero_sdk_python.hapi.services import token_wipe_account_pb2, transaction_pb2

## [0.1.4] - 2025-08-19

### Added

- CONTRIBUTING.md: expanded documentation detailing various contribution processes in a step-by-step way. Includes new sections: blog posts and support.
- README_upstream.md: documentation explaining how to rebase to main.

### Added

- Legacy ECDSA DER parse support
- documented private key from_string method behavior
- ContractInfo class
- ContractInfoQuery class
- ContractID check in PublicKey.\_from_proto() method
- PendingAirdropId Class
- PendingAirdropRecord Class
- TokenCancelAirdropTransaction Class
- AccountUpdateTransaction class
- ContractBytecodeQuery class
- SimpleStorage.bin-runtime
- Support for both .bin and .bin-runtime contract bytecode extensions in contract_utils.py
- ContractUpdateTransaction class

### Fixed

- missing ECDSA support in query.py and contract_create_transaction.py (was only creating ED25519 keys)
- Applied linting and code formatting across the consensus module
- fixed pip install hiero_sdk_python -> pip install hiero-sdk-python in README.md

### Breaking API changes

**We have several camelCase uses that will be deprecated → snake_case** Original aliases will continue to function, with a warning, until the following release.

#### In `token_info.py`

- tokenId → token_id
- totalSupply → total_supply
- isDeleted → is_deleted
- tokenType → token_type
- maxSupply → max_supply
- adminKey → admin_key
- kycKey → kyc_key
- freezeKey → freeze_key
- wipeKey → wipe_key
- supplyKey → supply_key
- defaultFreezeStatus → default_freeze_status
- defaultKycStatus → default_kyc_status
- autoRenewAccount → auto_renew_account
- autoRenewPeriod → auto_renew_period
- pauseStatus → pause_status
- supplyType → supply_type

#### In `nft_id.py`

- tokenId → token_id
- serialNumber → serial_number

#### In `transaction_receipt.py`

- tokenId → token_id
- topicId → topic_id
- accountId → account_id
- fileId → file_id

### Deprecated Additions

- logger.warn will be deprecated in v0.1.4. Please use logger.warning instead.
- get_logger method passing (name, level) will be deprecated in v0.1.4 for (level, name).

## [0.1.3] - 2025-07-03

### Added

- TokenType Class
- MAINTAINERS.md file
- Duration Class
- NFTTokenCreateTransaction Class
- TokenUnfreezeTransaction
- Executable Abstraction
- Logger
- Node Implementation
- Integration Tests across the board
- TokenWipeTransaction Class
- TokenNFTInfoQuery Class
- TokenInfo Class
- TokenRejectTransaction Class
- TokenUpdateNftsTransaction Class
- TokenInfoQuery Class
- TokenPauseTransaction Class
- TokenBurnTransaction Class
- TokenGrantKycTransaction Class
- TokenUpdateTransaction Class
- added Type hinting and initial methods to several modules
- TokenRevoceKycTransaction Class
- [Types Guide](hiero/hedera_sdk_python/documentation/sdk_developers/types.md)

- TransactionRecordQuery Class
- AccountInfoQuery Class

### Changed

- replace datetime.utcnow() with datetime.now(timezone.utc) for Python 3.10
- updated pr-checks.yml
- added add_require_frozen() to Transaction Base Class
- added NFT Transfer in TransferTransaction
- bumped solo-actions to latest release
- updated to/from_proto method to be protected
- Example scripts updated to be easily run form root
- README updated
- added PublicKey.from_proto to PublicKey class
- changed Query Class to have method get_cost
- SimpleContract and StatefulContract constructors to be payable
- added new_pending_airdrops to TransactionRecord Class
- Reorganized SDK developer documentation:
    - Renamed and moved `README_linting.md` to `linting.md`
    - Renamed and moved `README_types.md` to `types.md`
    - Renamed and moved `Commit_Signing.md` to `signing.md`
- Created `sdk_users` docs folder and renamed `examples/README.md` to `running_examples.md`
- Updated references and links accordingly

### Fixed

- fixed INVALID_NODE_ACCOUNT during node switching
- fixed ed25519 key ambiguity (PrivateKey.from_string -> PrivateKey.from_string_ed25519 in examples)

### Removed

- Redundant test.py file

## [0.1.2] - 2025-03-12

### Added

- NFTId Class

### Changed

- use SEC1 ECPrivateKey instead of PKCS#8

### Fixed

- PR checks
- misnamed parameter (ECDSASecp256k1=pub_bytes -> ECDSA_secp256k1=pub_bytes)

### Removed

- .DS_store file

## [0.1.1] – 2025-02-25

### Added

- RELEASE.md
- CONTRIBUTING.md

### Changed

- README now split into root README for project overview and /examples README for transaction types and syntax.
- Python version incremented from 3.9 to 3.10

### Removed

- pdm.lock & uv.lock file

## [0.1.0] - 2025-02-19

### Added

- Initial release of the Python SDK core functionality.
- Basic documentation on how to install and use the SDK.
- Example scripts illustrating setup and usage.

### Changed

- N/A

### Fixed

- N/A

### Removed

- N/A


# [0.1.0] - 2025-02-19
