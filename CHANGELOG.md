This is a markdown file, click Ctrl+Shift+V to view or click open preview.

# Changelog

All notable changes to this project will be documented in this file.  
This project adheres to [Semantic Versioning](https://semver.org).  
This changelog is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Legacy ECDSA DER parse support
- documented private key from_string method behavior
- ContractInfo class
- ContractInfoQuery class
- ContractID check in PublicKey._from_proto() method

### Fixed
- missing ECDSA support in query.py and contract_create_transaction.py (was only creating ED25519 keys)

### Changed
- SimpleContract and StatefulContract constructors to be payable

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
- README_types.md
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
