# Hiero Python SDK Examples

This directory contains comprehensive examples demonstrating how to use the Hiero Python SDK for various Hedera network operations. The examples cover account management, token operations, smart contracts, file operations, and more.

## Quick Start

1. **Install dependencies**: `pip install hiero-sdk-python python-dotenv`
2. **Set up credentials**: `cd examples && python3 setup_env.py`
3. **Run an example**: `python3 account_create.py`

That's it! The setup script will guide you through getting your testnet credentials and creating the necessary configuration files.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
- [Environment Configuration](#environment-configuration)
- [Getting Testnet Credentials](#getting-testnet-credentials)
- [Running Examples](#running-examples)
- [Example Categories](#example-categories)
- [Syntax Styles](#syntax-styles)

## Prerequisites

Before running the examples, ensure you have:

1. **Python 3.8+** installed on your system
2. **pip** (Python package installer)
3. **Hiero Python SDK** installed:
   ```bash
   pip install hiero-sdk-python
   ```
4. **python-dotenv** for environment variable management:
   ```bash
   pip install python-dotenv
   ```

## Setup Instructions

### 1. Clone the Repository

If you haven't already, clone the Hiero SDK repository:
```bash
git clone https://github.com/hashgraph/hiero-sdk-python.git
cd hiero-sdk-python
```

### 2. Install Dependencies

Install the required dependencies:
```bash
pip install -r requirements.txt
# or install the SDK directly
pip install hiero-sdk-python python-dotenv
```

## Environment Configuration

### 1. Create .env File

Create a `.env` file in the `/examples` directory. You have two options:

#### Option A: Use the Setup Script (Recommended)
```bash
cd examples
python3 setup_env.py
```
This interactive script will guide you through entering your credentials and create the `.env` file automatically.

#### Option B: Create Manually
```bash
cd examples
touch .env
```

### 2. Add Environment Variables

If you chose Option B, add the following variables to your `.env` file:

```env
# Your Hedera testnet account credentials
OPERATOR_ID=0.0.123456
OPERATOR_KEY=302e020100300506032b6570042204201234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef

# Optional: Network configuration (defaults to testnet)
NETWORK=testnet
```

**Important Security Notes:**
- Never commit your `.env` file to version control
- Keep your private keys secure and never share them
- Use testnet credentials for examples (not mainnet)

## Getting Testnet Credentials

### 1. Create a Hedera Portal Account

1. Visit [Hedera Portal](https://portal.hedera.com/)
2. Sign up for a free account
3. Verify your email address

### 2. Create a Testnet Account

1. Log in to the Hedera Portal
2. Navigate to the "Testnet" section
3. Click "Create Account"
4. Choose your preferred key type (ED25519 recommended)
5. Download your account credentials

### 3. Extract Your Credentials

From your downloaded credentials, you'll need:

- **Account ID**: Format `0.0.XXXXX` (e.g., `0.0.123456`)
- **Private Key**: A long hexadecimal string (e.g., `302e020100300506032b657004220420...`)

### 4. Add to .env File

Update your `.env` file with your actual credentials:

```env
OPERATOR_ID=0.0.123456
OPERATOR_KEY=302e020100300506032b657004220420your_actual_private_key_here
```

## Running Examples

### Basic Example Execution

Navigate to the examples directory and run any example:

```bash
cd examples
python3 account_create.py
```

### Example Categories

The examples are organized by functionality:

#### Account Operations
```bash
python3 account_create.py          # Create a new account
python3 account_update.py          # Update account properties
python3 query_account_info.py      # Query account information
python3 query_balance.py           # Query account balance
```

#### Token Operations
```bash
python3 token_create_fungible_infinite.py    # Create fungible token
python3 token_create_nft_infinite.py         # Create NFT token
python3 token_mint_fungible.py               # Mint fungible tokens
python3 token_mint_non_fungible.py           # Mint NFTs
python3 token_transfer.py                    # Transfer tokens
python3 token_associate.py                   # Associate token with account
```

#### Smart Contract Operations
```bash
python3 contract_create.py                   # Deploy smart contract
python3 contract_execute.py                  # Execute contract function
python3 contract_update.py                   # Update contract
python3 query_contract_info.py               # Query contract information
```

#### File Operations
```bash
python3 file_create.py                       # Create a file
python3 file_update.py                       # Update file contents
python3 file_append.py                       # Append to file
python3 file_delete.py                       # Delete a file
```

#### Topic Operations
```bash
python3 topic_create.py                      # Create a topic
python3 topic_message_submit.py              # Submit message to topic
python3 topic_update.py                      # Update topic properties
python3 topic_delete.py                      # Delete a topic
```

#### HBAR Transfers
```bash
python3 transfer_hbar.py                     # Transfer HBAR between accounts
```

### Troubleshooting

#### Common Issues

1. **"OPERATOR_ID not found" error**
   - Ensure your `.env` file exists in the `/examples` directory
   - Check that `OPERATOR_ID` is set correctly

2. **"OPERATOR_KEY not found" error**
   - Verify your private key is correctly copied to the `.env` file
   - Ensure there are no extra spaces or characters

3. **"Transaction failed" errors**
   - Check your account has sufficient HBAR for transaction fees
   - Verify you're using testnet credentials (not mainnet)
   - Ensure your account is active and not frozen

4. **Import errors**
   - Make sure you have installed the SDK: `pip install hiero-sdk-python`
   - Install python-dotenv: `pip install python-dotenv`

#### Getting Help

- Check the [Hedera Documentation](https://docs.hedera.com/)
- Visit the [Hedera Discord](https://discord.gg/hedera)
- Review the [SDK Documentation](https://docs.hedera.com/hedera/sdks-and-apis/sdks/python)

## Syntax Styles

The examples demonstrate two different syntax styles supported by the Hiero Python SDK:

### Pythonic Syntax
```python
transaction = AccountCreateTransaction(
    key=new_account_public_key,
    initial_balance=initial_balance,
    memo="Test Account"
).freeze_with(client)
```

### Method Chaining
```python
transaction = (
    AccountCreateTransaction()
    .set_key(new_account_public_key)
    .set_initial_balance(initial_balance)
    .set_account_memo("Test Account")
    .freeze_with(client)
)
```

Both styles are equivalent - choose the one that feels more natural to you!

## Contributing

If you find issues with the examples or want to add new ones:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

For more detailed contribution guidelines, see the main [CONTRIBUTING.md](../CONTRIBUTING.md) file.
