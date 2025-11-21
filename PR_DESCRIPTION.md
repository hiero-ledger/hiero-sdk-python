# PR: Add Token KYC Key Example for Hiero Python SDK

## 📋 Description

This PR adds a comprehensive example demonstrating Token KYC (Know Your Customer) key functionality in the Hiero Python SDK. The example provides clear, educational guidance on creating tokens with KYC keys, granting/revoking KYC status, and understanding how KYC affects token transfers.

## 🎯 Motivation

The KYC key is a critical administrative feature in Hedera tokens that controls account eligibility to hold and transfer tokens. The SDK was missing a dedicated, beginner-friendly example showing:

- How to create tokens with and without KYC keys
- Why KYC keys are essential for KYC operations
- How KYC status affects token transfers
- Best practices for KYC management

This addition fills an important gap in the SDK's documentation and learning resources.

## ✨ What's Included

### New File: `examples/token_create_transaction_kyc_key.py` (519 lines)

A comprehensive, production-ready example demonstrating:

#### **1. Token Creation Scenarios**

- `create_token_without_kyc_key()` - Create a token without KYC requirements
- `create_token_with_kyc_key()` - Create a token with proper KYC key setup
- Shows that both the operator and KYC key must sign token creation with KYC keys

#### **2. KYC Operations**

- `attempt_kyc_without_key()` - Demonstrates expected failure when KYC key is absent
- `grant_kyc_to_account()` - Properly grants KYC using the KYC key
- `revoke_kyc_from_account()` - Shows KYC revocation (bonus feature)

#### **3. Token Transfers & KYC Requirements**

- `attempt_transfer_without_kyc()` - Shows transfer attempts before KYC grant
- `transfer_token_after_kyc()` - Demonstrates successful transfer after KYC
- Balance querying to verify transfer success/failure

#### **4. Helper Functions**

- `setup_client()` - Initialize Hedera SDK client
- `create_account()` - Generate test accounts with initial HBAR balance
- `associate_token_to_account()` - Token association prerequisite

#### **5. Educational Output**

- Clear 7-step workflow with section headers
- Status codes and error messages for each operation
- Summary explaining KYC key behavior and key takeaways
- Inline comments explaining critical concepts

## 🔑 Key Takeaways Demonstrated

1. **KYC Keys are Essential** - Without a KYC key, KYC operations cannot be performed on a token
2. **Key Signing Requirements** - When creating tokens with KYC keys, both the operator and KYC key must sign
3. **Transfer Requirements** - Accounts typically cannot transfer tokens without KYC unless configured otherwise
4. **KYC Persistence** - Previously granted KYC remains even if the KYC key is later removed
5. **Key Independence** - KYC keys are independent of other token keys (admin key, freeze key, supply key)

## 🏗️ Implementation Details

### Code Quality

✅ Comprehensive error handling with try-catch blocks  
✅ Status code checking on all transactions  
✅ Clear, descriptive error messages  
✅ Proper resource cleanup  
✅ Python 3.10+ compatibility

### Documentation

✅ Detailed docstrings for all functions  
✅ Inline comments for critical operations  
✅ Clear section headers and progress indicators  
✅ Runnable with standard SDK setup

### Consistency

✅ Follows established example patterns from the repository  
✅ Uses same import structure as other token examples  
✅ Consistent naming conventions  
✅ Compatible with both `uv run` and `python` execution

## 📝 Testing Instructions

### Prerequisites

1. Hedera testnet account with HBAR balance
2. SDK installed: `pip install -e .`
3. Environment variables configured in `.env`:
   ```
   OPERATOR_ID=0.0.xxxx
   OPERATOR_KEY=302e020100...
   ```

### Run the Example

```bash
# Option 1: Using uv
uv run examples/token_create_transaction_kyc_key.py

# Option 2: Using Python
python examples/token_create_transaction_kyc_key.py
```

### Expected Output

- Token creation without KYC (Step 1)
- Failed KYC grant attempt on token without KYC key (Step 2)
- Token creation with KYC key (Step 3)
- Account creation and token association (Step 4)
- Transfer attempt before KYC grant (Step 5)
- KYC grant to account (Step 6)
- Successful transfer after KYC (Step 7)
- Final summary with key takeaways

## 📚 Related Examples

This example complements existing token key examples:

- `examples/token_create_transaction_admin_key.py` - Admin key privileges
- `examples/token_create_transaction_freeze_key.py` - Freeze key behavior
- `examples/token_create_transaction_supply_key.py` - Supply key management

## 🔄 Changes Summary

- **Added**: `examples/token_create_transaction_kyc_key.py` (519 lines)
- **Updated**: `CHANGELOG.md` - Added entry to "Unreleased" section under "Added"

## ✅ Checklist

- [x] Code follows SDK conventions and patterns
- [x] All functions include comprehensive docstrings
- [x] Error handling implemented throughout
- [x] Example is self-contained and runnable
- [x] CHANGELOG.md updated
- [x] Syntax validation passed
- [x] Imports verified against existing examples
- [x] Documentation includes clear instructions
- [x] Educational value for new SDK users

## 📖 References

- [Hedera Token Service Documentation](https://docs.hedera.com/hedera/sdks-and-apis/sdks/hapi-overview)
- [KYC Key Behavior](https://docs.hedera.com/hedera/sdks-and-apis/sdks/hapi-overview)
- Related SDK Examples in `examples/` directory

## 🤝 Notes for Reviewers

- The example prioritizes **educational clarity** over brevity
- Step-by-step workflow helps new developers understand KYC requirements
- Both success and failure scenarios are demonstrated
- The example is production-ready but designed for learning purposes
- All operations include proper error handling and status checking
