# Test Suite Quick Reference

## Run Tests

```bash
.github/scripts/test-bot-inactivity-unassign.sh
```

## Test Summary

| Test | Description | Validates |
|------|-------------|-----------|
| 1 | PR with discussion label | Label is detected, PR not closed |
| 2 | Stale PR without discussion | No label detected, eligible for close |
| 3 | jq filter correctness | Proper label extraction |
| 4 | Closed PR handling | Closed PRs are skipped |
| 5 | Active PR handling | Recent commits prevent closure |
| 6 | Log message format | Correct skip message format |
| 7 | Multiple labels | Discussion found among many labels |
| 8 | Case sensitivity | Only lowercase 'discussion' matches |

## Key Validation Points

### ✅ Discussion Label Protection
```bash
# This check protects PRs from auto-close
HAS_DISCUSSION_LABEL=$(gh pr view "$PR_NUM" --repo "$REPO" --json labels --jq '.labels[].name | select(. == "discussion")')
if [[ -n "$HAS_DISCUSSION_LABEL" ]]; then
  echo "    [SKIP] PR #$PR_NUM has 'discussion' label, keeping open"
  continue
fi
```

### ✅ Expected Log Output
```
[SKIP] PR #123 has 'discussion' label, keeping open
```

### ✅ Case Sensitive Matching
- ✓ `discussion` → Matches (protected)
- ✗ `Discussion` → Does not match (not protected)
- ✗ `DISCUSSION` → Does not match (not protected)

## Expected Results

When running the test suite, you should see:

```
Total tests run:    11
Tests passed:       11
All tests passed!
```

Exit code: `0`

## Dependencies

- `bash` or `zsh` shell
- `jq` (JSON processor)
- Standard Unix utilities: `date`, `grep`, `sed`

## Quick Install jq

```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq

# Fedora/RHEL
sudo dnf install jq
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Permission denied | `chmod +x .github/scripts/test-bot-inactivity-unassign.sh` |
| jq not found | Install jq (see above) |
| Tests fail | Check detailed output for specific failure reason |

## Files

- **Test Script:** `.github/scripts/test-bot-inactivity-unassign.sh`
- **Main Script:** `.github/scripts/bot-inactivity-unassign.sh`
- **Documentation:** `.github/scripts/TEST_DOCUMENTATION.md`
- **Quick Reference:** `.github/scripts/TEST_QUICK_REFERENCE.md` (this file)

## CI Integration

Add to your GitHub workflow:

```yaml
- name: Run Bot Tests
  run: |
    chmod +x .github/scripts/test-bot-inactivity-unassign.sh
    .github/scripts/test-bot-inactivity-unassign.sh
```

---

For detailed information, see [TEST_DOCUMENTATION.md](TEST_DOCUMENTATION.md)
