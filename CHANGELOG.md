This is a markdown file, click Ctrl+Shift+V to view or click open preview.

# Changelog

All notable changes to this project will be documented in this file.  
This project adheres to [Semantic Versioning](https://semver.org).  
This changelog is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]
### Added
- ContractDeleteTransaction class
- ContractExecuteTransaction class
- setMessageAndPay() function in StatefulContract
- AccountDeleteTransaction Class

### Changed
- bump solo version to `v0.12`
- Extract Ed25519 byte loading logic into private helper method `_from_bytes_ed25519()`
- Incorrect naming in README for generate_proto.py to generate_proto.sh
- Changed README MIT license to Apache
- Documentation structure updated: contents moved from `/documentation` to `/docs`.

### Removed
- Removed the old `/documentation` folder.
- Rebase command in README_upstream changed to just -S

## [0.1.4] - 2025-08-19
### Added
- CONTRIBUTING.md: expanded documentation detailing various contribution processes in a step-by-step way. Includes new sections: blog posts and support.
- README_upstream.md: documentation explaining how to rebase to main.

### Added
- Legacy ECDSA DER parse support
- documented private key from_string method behavior
- ContractInfo class
- ContractInfoQuery class
- ContractID check in PublicKey._from_proto() method
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
