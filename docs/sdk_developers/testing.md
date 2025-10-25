# SDK Developer Testing Guide

Testing is an essential and mandatory step when creating new functionality for the Hiero Python SDK. We require all new features to be covered by robust unit tests and integration tests to ensure code reliability and maintainability.

Unit tests are straightforward to run and verify locally on your development machine. Integration tests can be mocked locally, but are automatically executed against a solo network when you submit a branch as a pull request (PR).

This guide explains what unit and integration tests are, and details how to set up your local unit testing suite and complete integration tests successfully.

---

## 🧭 Table of Contents

1. [Explaining Unit Tests](#explaining-unit-tests)
2. [Explaining Integration Tests](#explaining-integration-tests)
3. [Setting Up a Local Testing Suite](#setting-up-a-local-testing-suite)
    * [VS Code](#vs-code)
    * [From Bash](#from-bash)
4. [Running Integration Tests](#running-integration-tests)