# Changelog

All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](https://semver.org).
This changelog is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

- Refactor `query_balance.py` into modular, reusable functions with `setup_client()`, `create_account()`, `get_balance()`, `transfer_hbars()`, and `main()` for improved readability, maintainability, and error handling.
- Unified balance and transfer logging format — both now consistently display values in hbars for clarity.

### Added
- Refactored `examples/topic_create.py` into modular functions for better readability and reuse.
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
- **docs:** Added comprehensive Google-style docstrings to the `AccountInfo` model’s predefined conversion methods (`_from_proto` and `_to_proto`) for improved clarity and maintainability. (#562)

### Changed
- Renamed `examples/nft_allowance.py` to `examples/account_allowance_nft.py` for consistency with account class naming scheme
- Added changelog conflict resolution examples to `docs/common_issues.md`
- Refactored `examples/topic_create.py` to be more modular by splitting functions and renaming `create_topic()` to `main()`.
- Refactored `examples/transfer_hbar.py` to improve modularity by separating transfer and balance query operations into dedicated functions
- Enhanced contributing section in README.md with resource links
- Refactored examples/topic_message_submit.py to be more modular
- Added "One Issue Per Pull Request" section to `examples/sdk_developers/common_issues.md`.
- docs: Improved the contributing section in the README.md file
- Refactored `examples/transfer_nft.py` to be more modular by isolating transfer logic.
- Renamed `examples/hbar_allowance.py` to `examples/account_allowance_hbar.py` for naming consistency
- Converted monolithic function in `token_create_nft_infinite.py` to multiple modular functions for better structure and ease.
- docs: Use relative paths for internal GitHub links (#560).

### Fixed
- Add type hints to `setup_client()` and `create_new_account()` functions in `examples/account_create.py` (#418)
- Added explicit read and write permissions to test.yml

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

### Changed
- TransferTransaction refactored to use TokenTransfer and HbarTransfer classes instead of dictionaries
- Added checksum validation for TokenId
- Refactor examples/token_cancel_airdrop
- Refactor token creation examples for modularity and consistency
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
- src/hiero_sdk_python/tokens/__init__.py: content removed.
- src/hiero_sdk_python/tokens/token_info.py: from hiero_sdk_python.hapi.services.token_get_info_pb2 import TokenInfo as proto_TokenInfo → from hiero_sdk_python.hapi.services import token_get_info_pb2
- src/hiero_sdk_python/tokens/token_key_validation.py: from hiero_sdk_python.hapi.services → import basic_types_pb2
- src/hiero_sdk_python/tokens/token_kyc_status.py: from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenKycStatus as proto_TokenKycStatus → from hiero_sdk_python.hapi.services import basic_types_pb2
- src/hiero_sdk_python/tokens/token_pause_status.py: from hiero_sdk_python.hapi.services.basic_types_pb2 import (TokenPauseStatus as proto_TokenPauseStatus,) → from hiero_sdk_python.hapi.services import basic_types_pb2
- src/hiero_sdk_python/tokens/token_pause_transaction.py: from hiero_sdk_python.hapi.services.token_pause_pb2 import TokenPauseTransactionBody → from hiero_sdk_python.hapi.services import token_pause_pb2, transaction_pb2
- from hiero_sdk_python.hapi.services.token_revoke_kyc_pb2 import TokenRevokeKycTransactionBody → from hiero_sdk_python.hapi.services import token_revoke_kyc_pb2, transaction_pb2
- src/hiero_sdk_python/tokens/token_update_nfts_transaction.py: from hiero_sdk_python.hapi.services.token_update_nfts_pb2 import TokenUpdateNftsTransactionBody → from hiero_sdk_python.hapi.services import token_update_nfts_pb2,transaction_pb2
- src/hiero_sdk_python/tokens/token_wipe_transaction.py: from hiero_sdk_python.hapi.services.token_wipe_account_pb2 import TokenWipeAccountTransactionBody → from hiero_sdk_python.hapi.services import token_wipe_account_pb2, transaction_pb2

## [0.1.4] - 2025-08-19
...
