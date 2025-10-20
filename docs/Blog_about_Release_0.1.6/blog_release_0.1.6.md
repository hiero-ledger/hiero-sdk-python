# 🚀 Hiero Python SDK – Announcing Release v0.1.6

Announcing the **version 0.1.6** of the Hiero Python SDK!  
In this release introducing powerful new transaction capabilities, improved allowance management, and refinements across multiple SDK examples - making development on Hedera even better for Python users.
A huge thank you to our talented contributors for making this release possible.. ❤️

---

## ✨ What’s New in 0.1.6

This release expands the SDK’s transaction and topic management features, giving developers more flexibility and precision when interacting with Hedera.

### 🧾 New Features
- **Revenue-Generating Topic Examples:** Explore new topic tests and examples to better understand revenue-based use cases.
- **Enhanced Topic APIs:** Added `TopicCreate`, `TopicUpdate`, and `TopicInfo` transactions with new parameters:
  - `fee_schedule_key`
  - `fee_exempt_keys`
  - `custom_fees`
- **New Classes and Transactions:**
  - `CustomFeeLimit`
  - `TokenNftAllowance`
  - `TokenAllowance`
  - `HbarAllowance`
  - `HbarTransfer`
  - `AccountAllowanceApproveTransaction`
  - `AccountAllowanceDeleteTransaction`
- **Approved Transfer Support:** `TransferTransaction` now supports approved transfers.
- **New API Utility:** Added `Transaction.set_transaction_id()` for finer transaction control.
- **Allowance Examples:** Check out new practical examples:
  - `hbar_allowance.py`
  - `token_allowance.py`
  - `nft_allowance.py`

---

## 🔄 Improvements & Changes
We’ve streamlined the SDK’s internal handling and improved code readability across key modules.

- `TransferTransaction` now uses `TokenTransfer` and `HbarTransfer` classes instead of dicts, offering a cleaner and more structured approach.
- Added **checksum validation** for `TokenId` for safer and more reliable operations.
- Refactored examples for better readability and consistency:
  - `token_cancel_airdrop.py`
  - `token_associate.py` (now includes association verification query – #367)
  - `account_create.py` (enhanced modularity and readability – #363)

---

## 🐞 Fixes
- Fixed a **type assignment issue** in `token_transfer_list.py`.
- Corrected internal method references (`__require_not_frozen()` → `_require_not_frozen()`).
- Removed redundant `_is_frozen` method to reduce internal complexity.

---

## ⚡ Upgrade to the Latest Version

Update to the latest Hiero Python SDK release with:

```bash
pip install --upgrade hiero-sdk-python
```

Then try out contract creation, account updates, or file queries directly in your Python environment.
You can also check out our open issues (for both new starters and seasoned Python developers):
👉[GitHub Issues](https://github.com/hiero-ledger/hiero-sdk-python/issues)
