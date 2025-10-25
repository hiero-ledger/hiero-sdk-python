# Testing Guide for SDK Developers

## Introduction

Testing is an essential and mandatory part of contributing new functionality to the Hiero Python SDK. We require that all new features and bug fixes be accompanied by both **unit tests** and **integration tests** to ensure the reliability and integrity of the SDK.

Unit tests are fast and easy to run locally on your machine. Integration tests, which simulate real network interactions, can be run using a local mock environment, but they are primarily executed against a complete, dedicated solo network automatically when you submit a Pull Request.

This guide is designed to explain the purpose of unit and integration tests, and provide clear instructions on how to set up and run them locally to validate your work before submission.

## Table of Contents

- [Explaining Unit Tests](#explaining-unit-tests)
- [Explaining Integration Tests](#explaining-integration-tests)
- [Setting Up a Local Testing Suite](#setting-up-a-local-testing-suite)
    - [Using VS Code](#using-vs-code)
    - [From Bash](#from-bash)
- [Running Integration Tests](#running-integration-tests)