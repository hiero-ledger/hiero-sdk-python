# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## UNRELEASED

### Added

- Added `_from_protobuf` inverse-serialization support for `TokenMintTransaction`, `TokenBurnTransaction`, and `TokenWipeTransaction` to enable complete reconstruction and round-trip fidelity via `Transaction.from_bytes()`.
