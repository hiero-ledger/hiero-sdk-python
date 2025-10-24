# Changelog

All notable changes to this project will be documented in this file.  
This project adheres to [Semantic Versioning](https://semver.org).  
This changelog is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Refactor `query_balance.py` into modular, reusable functions with `setup_client()`, `create_account()`, `get_balance()`, `transfer_hbars()`, and `main()` for improved readability, maintainability, and error handling.
- Unified balance and transfer logging format — both now consistently display values in hbars for clarity.
- Add `examples/account_id.py` demonstrating AccountId class usage including creating standard AccountIds, parsing from strings, comparing instances, and creating AccountIds with public key aliases.
- Google-style docstrings added to `CustomFractionalFee`, `CustomFixedFee`, `CustomRoyaltyFee`, and `AbstractTokenTransferTransaction` classes and their methods.
- Added `dependabot.yaml` for automated dependency management.
- Common issues guide for SDK developers at `examples/sdk_developers/common_issues.md`.
- Documentation for resolving changelog conflicts in `docs/common_issues.md`.
- Comprehensive changelog entry guide at `docs/sdk_developers/changelog.md` (#532).

### Changed
- Refactored examples for modularity and consistency:
  - `examples/topic_create.py` → split functions, renamed `create_topic()` to `main()`.
  - `examples/transfer_hbar.py` → separated transfer and balance query operations.
  - `examples/topic_message_submit.py` → improved modularity.
  - `examples/transfer_nft.py` → isolated transfer logic.
- Enhanced contributing section in README.md with resource links.
- Added "One Issue Per Pull Request" section to `examples/sdk_developers/common_issues.md`.
- Refactored `examples/transfer_nft.py` to be more modular by isolating transfer logic.
- Renamed `examples/hbar_allowance.py` to `examples/account_allowance_hbar.py` for naming consistency.
- Improved contributing section in README.md.

### Fixed
- Added type hints to `setup_client()` and `create_new_account()` functions in `examples/account_create.py` (#418).
- Explicit read and write permissions added to `test.yml`.

## [0.1.6] - 2025-10-21

### Added
- `TokenFeeScheduleUpdateTransaction` to update token fee schedules (#471).
- Google-style docstrings for `examples/account_create.py`.
- Revenue-generating topic tests/examples.
- Added `fee_schedule_key`, `fee_exempt_keys`, and `custom_fees` fields in `TopicCreateTransaction`, `TopicUpdateTransaction`, `TopicInfo` classes.
- Added classes: `CustomFeeLimit`, `TokenNftAllowance`, `TokenAllowance`, `HbarAllowance`, `HbarTransfer`.
- Added transaction classes: `AccountAllowanceApproveTransaction`, `AccountAllowanceDeleteTransaction`, `FileAppendTransaction`.
- Documentation examples for Allowance Approve/Delete and File Append transactions.
- Approved transfer support in `TransferTransaction`.
- `set_transaction_id()` API added to `Transaction` class.
- Allowance examples: `hbar_allowance.py`, `token_allowance.py`, `nft_allowance.py`.

### Changed
- `TransferTransaction` refactored to use `TokenTransfer` and `HbarTransfer` classes instead of dictionaries.
- Checksum validation added for `TokenId`.
- Refactored `examples/token_cancel_airdrop` and token creation examples for modularity.
- Rearranged `running_examples.md` alphabetically.
- Refactored `token_associate.py` for better structure and added association verification query (#367).
- Refactored `examples/account_create.py` for modularity and readability (#363).
- Maintainers updated: Hendrik Ebbers → Sophie Bulloch.
- `CONTRIBUTING.md` improved with `/docs` folder structure and fixed broken hyperlinks (#431).
- Converted class in `token_nft_info.py` to dataclass.

### Fixed
- Incompatible type assignments in `token_transfer_list.py`.
- Corrected references to `_require_not_frozen()` and removed surplus `_is_frozen`.
- Removed duplicate static methods in `TokenInfo` class:
  - `_copy_msg_to_proto`
  - `_copy_key_if_present`
  - `_parse_custom_fees`
- Strict type hints added to `TransactionGetReceiptQuery` (#420).
- Fixed broken documentation links in `CONTRIBUTING.md`.
- Updated all documentation references to use local paths.

## [0.1.5] - 2025-09-25

### Added
- Schedule, Node, Contract, and Account transaction/query classes (ScheduleSignTransaction, NodeUpdateTransaction, ContractExecuteTransaction, etc.).
- PRNG properties in `TransactionRecord`.
- Ethereum transaction support and ECDSA alias accounts.
- Example scripts for Token Airdrop and allowance transactions.
- Dependency groups `dev` and `lint` in `pyproject.toml`.
- Bumped Hedera proto version: v0.57.3 → v0.64.3.
- CI tests for Python 3.10–3.12.
- Documentation restructuring: `/documentation` → `/docs`.

### Changed
- Solo and protobuf versions bumped.
- Transaction body proto extraction refactored.
- Mirror Node endpoints updated to secure URLs.
- PrivateKey handling generalized (`from_string`).
- StatefulContract modifications for general access.
- Various example scripts updated for modularity and consistency.

### Fixed
- Formatting and type hints in multiple example files.
- Windows path issues fixed.
- Signature validation and hex representations corrected.
- Duplicate validation functions removed.

### Removed
- Old `/documentation` folder.
- `generate_proto.sh`.
- `pkg_resources` dependency in `generate_proto.py`.

### Breaking API changes
- Proto imports updated due to version bump.
- Removed content in `/tokens/__init__.py`.
- Various import paths updated across SDK modules.

---

> Previous versions [0.1.4] → [0.1.0] retained as in original changelog.
