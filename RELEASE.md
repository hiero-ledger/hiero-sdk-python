# Release Process for the Hiero Python SDK

This document describes how we handle versioning and publishing new releases of the Hiero Python SDK.

## Semantic Versioning

We use [Semantic Versioning](https://semver.org) for this project:

```
MAJOR.MINOR.PATCH
```

- **MAJOR**: Breaking changes
- **MINOR**: Backward-compatible new features
- **PATCH**: Bug fixes and other minor changes

## Release Steps

1. **Update the Version**
   Decide whether the changes are major, minor, or patch increments.

2. **Update the Changelog**
   Move your entries from the **[Unreleased]** section in `CHANGELOG.md` to a new version heading with today’s date (e.g., `## [0.2.0] - 2025-02-20`).

3. **Create a Release Branch**
   - `release-v0.2.0` or similar (e.g., `release-v0.2.0-beta.1` for beta versions).

4. **Run Tests**
   - Ensure all tests pass locally (run `pytest`).
   - Confirm CI passes (integration tests, etc.).

5. **Merge into `main`**
   - Create a Pull Request from `release-vX.X.X` into `main`.
   - Wait for code review, ensure everything is green.

6. **Tag the Release**
   Once merged, create a git tag with the new version:
   ```bash
   git tag -a v0.2.0 -m "Release 0.2.0"
   git push origin v0.2.0
   ```

4. **Monitor the Publish Workflow**
   - The `.github/workflows/publish.yml` workflow runs automatically when the tag is pushed.
   - The workflow builds the source distribution and wheel, generates protobufs before packaging, signs the release artifacts with Sigstore, publishes the package to PyPI, and creates or updates the GitHub release.

5. **Verify Published Artifacts**
   - Confirm the new version is available on PyPI.
   - Confirm the GitHub release contains the wheel, source distribution, and matching `.sigstore.json` bundles.
   - If release provenance needs to be audited, use the Sigstore verification materials attached to the GitHub release.
