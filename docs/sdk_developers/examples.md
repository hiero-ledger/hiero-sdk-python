# Running Examples

This guide will help you set up and run the Hiero SDK Python examples.

## Prerequisites

- Python 3.10 or higher
- `uv` package manager (recommended) or `pip`

For installation instructions, see the main [README.md](../../../../README.md).

## Environment Setup

Before running any examples, you need to set up your environment variables for testnet credentials.

### 1. Create Environment File

Create a `.env` file in the project root directory with your testnet credentials:

```bash
# Required testnet credentials
OPERATOR_ID=0.0.1234xx
OPERATOR_KEY=af20e47d590300506032b657004220420...
NETWORK=testnet

# Optional credentials (for advanced examples)
ADMIN_KEY=af20e47d59032b65700321009308ecfdf...
SUPPLY_KEY=302a300506032b6570032100c5e4af5...
FREEZE_KEY=302a300306072b65700321009308ecfdf...
RECIPIENT_ID=0.0.789xx
TOKEN_ID=0.0.100xx
TOPIC_ID=0.0.200xx
FREEZE_ACCOUNT_ID=0.0.100
```

**Important Notes:**
- These are **testnet credentials only** - they will not work on mainnet
- Get testnet credentials from the [Hedera Portal](https://portal.hedera.com/)
- Learn more about testnet [here](https://docs.hedera.com/guides/testnet)
- Only `OPERATOR_ID`, `OPERATOR_KEY`, and `NETWORK` are required for basic examples

### 2. Validate Your Setup

Run the environment setup script to validate your credentials:

```bash
# From project root
python docs/setup_env.py
```

This script will:
- Check if your `.env` file exists
- Validate your private key format
- Verify your account ID format
- Test network connectivity

### 3. Install Dependencies

If you haven't already, install the project dependencies:

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

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
NETWORK=testnet
```

## Running Examples

### Basic Examples

Start with these fundamental examples:

```bash
# Create a new account
python examples/account_create.py

# Query account balance
python examples/query_balance.py

# Transfer HBAR
python examples/transfer_hbar.py
```

### Token Examples

```bash
# Create a fungible token
python examples/token_create_fungible_infinite.py

# Mint tokens
python examples/token_mint_fungible.py

# Transfer tokens
python examples/transfer_token.py
```

### Advanced Examples

```bash
# Smart contract examples
python examples/contract_create.py
python examples/contract_execute.py

# Consensus service examples
python examples/topic_create.py
python examples/topic_message_submit.py
```

## Example Categories

The examples are organized by functionality:

### Account Operations
```bash
python examples/account_create.py          # Create a new account
python examples/account_update.py          # Update account properties
python examples/query_account_info.py      # Query account information
python examples/query_balance.py           # Query account balance
```

### Token Operations
```bash
python examples/token_create_fungible_infinite.py    # Create fungible token
python examples/token_create_nft_infinite.py         # Create NFT token
python examples/token_mint_fungible.py               # Mint fungible tokens
python examples/token_mint_non_fungible.py           # Mint NFTs
python examples/transfer_token.py                    # Transfer tokens
python examples/token_associate.py                   # Associate token with account
```

### Smart Contract Operations
```bash
python examples/contract_create.py                   # Deploy smart contract
python examples/contract_execute.py                  # Execute contract function
python examples/contract_update.py                   # Update contract
python examples/query_contract_info.py               # Query contract information
```

### File Operations
```bash
python examples/file_create.py                       # Create a file
python examples/file_update.py                       # Update file contents
python examples/file_append.py                       # Append to file
python examples/file_delete.py                       # Delete a file
```

### Topic Operations
```bash
python examples/topic_create.py                      # Create a topic
python examples/topic_message_submit.py              # Submit message to topic
python examples/topic_update.py                      # Update topic properties
python examples/topic_delete.py                      # Delete a topic
```

### HBAR Transfers
```bash
python examples/transfer_hbar.py                     # Transfer HBAR between accounts
```

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

## Troubleshooting

### Common Issues

1. **Invalid Private Key**: Ensure your private key is in the correct format (hex string or DER format)
2. **Network Connection**: Verify you're using `NETWORK=testnet` in your `.env` file
3. **Insufficient Balance**: Make sure your testnet account has sufficient HBAR for transactions
4. **Python Version**: Ensure you're using Python 3.10 or higher
5. **"OPERATOR_ID not found" error**
   - Ensure your `.env` file exists in the project root directory
   - Check that `OPERATOR_ID` is set correctly
6. **"OPERATOR_KEY not found" error**
   - Verify your private key is correctly copied to the `.env` file
   - Ensure there are no extra spaces or characters
7. **"Transaction failed" errors**
   - Check your account has sufficient HBAR for transaction fees
   - Verify you're using testnet credentials (not mainnet)
   - Ensure your account is active and not frozen
8. **Import errors**
   - Make sure you have installed the SDK: `pip install hiero-sdk-python`
   - Install python-dotenv: `pip install python-dotenv`

### Getting Help

- Check the [main README](../../../../README.md) for installation issues
- Review the [syntax examples](../sdk_users/running_examples.md) for code patterns
- Visit the [Hedera Documentation](https://docs.hedera.com/) for network details
- Check the [Hedera Discord](https://discord.gg/hedera)
- Review the [SDK Documentation](https://docs.hedera.com/hedera/sdks-and-apis/sdks/python)

## Security Notes

- **Never use mainnet credentials in examples**
- **Never commit your `.env` file to version control**
- **Testnet credentials are for development only**
- **Always validate transactions before signing**
- **Keep your private keys secure and never share them**

## Next Steps

After running the basic examples:

1. Explore the [syntax examples](../sdk_users/running_examples.md) to understand different coding patterns
2. Check out the [contract examples](examples/contracts/) for smart contract development
3. Review the [unit tests](../../../tests/) for more complex usage patterns
4. Read the [API documentation](https://docs.hedera.com/) for detailed reference

## Contributing

If you find issues with the examples or want to add new ones:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

For more detailed contribution guidelines, see the main [CONTRIBUTING.md](../../../../CONTRIBUTING.md) file.