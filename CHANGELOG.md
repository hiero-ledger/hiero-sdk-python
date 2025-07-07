# Changelog

All notable changes to this project will be documented in this file.  
This project adheres to [Semantic Versioning](https://semver.org).  
This changelog is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]
### Deprecated
- logger.warn is deprecated and will be removed in a future release. Please use logger.warning instead.
- get_logger method passing (name, level) will be removed in preference of (level, name) in a future release.


## [0.1.3]
### Added
- a lot of Transactions

### Changed
- Example scripts updated
- README updated

### Removed


## [0.1.1]
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
