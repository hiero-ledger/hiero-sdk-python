# Hiero SDK in Python

This is a Python SDK for interacting with the Hedera Hashgraph platform. It allows developers to:

- Manage Token Transactions like Create, Mint Fungible, Mint Non-Fungible, Associate, Dissociate, Transfer, Freeze, Unfreeze & Delete
- Manage Consensus Transactions like Topic Create, Update, Delete
- Submit Topic Messages
- Query Account Balance, Transaction Receipts, Topic Infos and Messages

## Table of Contents

- [Installation](#installation)
  - [Installing from PyPI](#installing-from-pypi)
  - [Installing from Source](#installing-from-source)
  - [Local Editable Installation](#local-editable-installation)
- [Environment Setup](#environment-setup)
- [Running Tests](#running-tests)
- [Usage](#usage)
  - [Creating an Account](#creating-an-account)
  - [Querying Account Balance](#querying-account-balance)
  - [Creating a Token](#creating-a-token)
  - [Minting a Fungible Token](#minting-a-fungible-token)
  - [Minting a Non-Fungible Token](#minting-a-non-fungible-token)
  - [Associating a Token](#associating-a-token)
  - [Dissociating a Token](#dissociating-a-token)
  - [Transferring Tokens](#transferring-tokens)
  - [Deleting a Token](#deleting-a-token)
  - [Freezing a Token](#freezing-a-token)
  - [Unfreezing a Token](#unfreezing-a-token)
  - [Transferring HBAR](#transferring-hbar)
  - [Creating a Topic](#creating-a-topic)
  - [Submitting a Topic Message](#submitting-a-topic-message)
  - [Updating a Topic](#updating-a-topic)
  - [Deleting a Topic](#deleting-a-topic)
  - [Querying Topic](#querying-topic)
  - [Querying Topic Message](#querying-topic-message)
- [Contributing](#contributing)

## Installation

### Installing from PyPI

The latest release of this SDK is published to PyPI. You can install it with:

```
pip install --upgrade pip
pip install hiero_sdk_python
```

This will pull down a stable release along with the required dependencies.


### Installing from Source

You can also clone the repo and install dependencies using uv:

1. Install `uv`:

`uv` is an ultra-fast Python package and project manager. It replaces `pip`, `pip-tools`, `pipx`, `poetry`, `pyenv`,
`virtualenv`, and more.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

If on macOS, you can also install `uv` using Homebrew:

```bash
brew install uv
```

Other installation methods can be found [here](https://docs.astral.sh/uv/getting-started/installation/).

2. Clone this repository:

```bash
git clone https://github.com/hiero-ledger/hiero_sdk_python.git
cd hiero-sdk-python
```

3. Install dependencies:

One of the really nice features of `uv` is that it will download and manage the correct version of python and build
with the correct version of python based on the `.python-version`  file in the project. This means you don't have to
worry about managing multiple versions of python on your machine!

```bash
uv sync
sh generate_proto.sh
```

To update to a newer version of the protobuf libraries, edit the `generate_proto.py` file and change the version number
and then rerun it.


### Local Editable Installation

For active development, you can install the repo in editable mode. That way, changes in your local code are immediately reflected when you import:

```
git clone https://github.com/hiero-ledger/hiero-sdk-python.git
cd hiero-sdk-python
pip install --upgrade pip
pip install -e .
```

Now you can run example scripts like python `examples/account_create.py`, and it will import from your local hiero_sdk_python code.


## Environment Setup

Before using the SDK, you need to configure your environment variables for the operator account and other credentials.
Create a .env file in the root of your project with the following (replace with your environment variables):

```
OPERATOR_ID=0.0.1234xx
OPERATOR_KEY=302e020100300506032b657004220420...
ADMIN_KEY=302a300506032b65700321009308ecfdf...
SUPPLY_KEY =302a300506032b6570032100c5e4af5..."
FREEZE_KEY=302a300306072b65700321009308ecfdf...
RECIPIENT_ID=0.0.789xx
TOKEN_ID=0.0.100xx
TOPIC_ID=0.0.200xx
FREEZE_ACCOUNT_ID=0.0.100
NETWORK=testnet
```

A [sample .env](.env.example) file is provided in the root of this project. If you do not have an account on
the Hedera testnet, you can easily get one from the [Hedera Portal](https://portal.hedera.com/). Learn more about
testnet [here](https://docs.hedera.com/guides/testnet).

## Running Tests

To run the test suite for the SDK, use the following command:
```
uv run pytest 
```

The test file in the root of this project will be automatically run when pushing onto a branch.
This is done by running 'Hedera Solo'. Read more about it here:

- [Github Marketplace](https://github.com/marketplace/actions/hedera-solo)
- [Blog Post by Hendrik Ebbers](https://dev.to/hendrikebbers/ci-for-hedera-based-projects-2nja)

#### Output:
```
Account creation successful. New Account ID: 0.0.5025xxx
New Account Private Key: 228a06c363b0eb328434d51xxx...
New Account Public Key: 8f444e36e8926def492adxxx...
Token creation successful. Token ID: 0.0.5025xxx
Token association successful.
Token dissociation successful.
Token minting successful.
Token transfer successful.
Token freeze successful.
Token unfreeze successful. 
Token deletion successful.
Topic creation successful.
Topic Message submitted.
Topic update successful.
Topic deletion successful.
```

## Syntax Flexibility

The Hedera SDK in Python supports two distinct syntax styles for creating and executing transactions:

- Pythonic Syntax: Ideal for developers who prefer explicit constructor-style initialization.
- Method Chaining: Provides a fluent API style for chaining methods, commonly used in many SDKs.

You can choose either syntax or even mix both styles in your projects.


## Usage

Below are examples of how to use the SDK for various operations. Each section provides both Pythonic syntax and method chaining examples.

### Creating an Account

#### Pythonic Syntax:
```
transaction = AccountCreateTransaction(
    key=new_account_public_key,
    initial_balance=initial_balance,
    memo="Test Account"
).freeze_with(client)

transaction.sign(operator_key)
transaction.execute(client)

```
#### Method Chaining:
```
transaction = (
        AccountCreateTransaction()
        .set_key(new_account_public_key)
        .set_initial_balance(initial_balance)
        .set_account_memo("Test")
        .freeze_with(client)
    )
    transaction.sign(client.operator_private_key)
    transaction.execute(client)
```

### Querying Account Balance

#### Pythonic Syntax:
```
balance = CryptoGetAccountBalanceQuery(account_id=some_account_id).execute(client) print(f"Account balance: {balance.hbars} hbars")
```

#### Method Chaining:
```
balance = ( CryptoGetAccountBalanceQuery() .set_account_id(some_account_id) .execute(client) ) print(f"Account balance: {balance.hbars} hbars")
```

### Creating a Token

#### Pythonic Syntax:
```
transaction = TokenCreateTransaction(
    token_name="ExampleToken",
    token_symbol="EXT",
    decimals=2,
    initial_supply=1000,
    treasury_account_id=operator_id,
    admin_key=admin_key
    supply_key=supply_key
).freeze_with(client)

transaction.sign(admin_key)
transaction.sign(operator_key)
transaction.execute(client)

```
#### Method Chaining:
```
transaction = (
        TokenCreateTransaction()
        .set_token_name("ExampleToken")
        .set_token_symbol("EXT")
        .set_decimals(2)
        .set_initial_supply(1000)
        .set_treasury_account_id(operator_id)
        .set_admin_key(admin_key) # Optional to create a token. Necessary for Token Delete or Update.
        .set_supply_key(supply_key) # Optional to change token supply. Necessary for Token Mint or Burn.
        .freeze_with(client)
    )

    transaction.sign(admin_key) # If admin key exists.
    transaction.sign(operator_key)
    transaction.execute(client)
```


### Minting a Fungible Token

#### Pythonic Syntax:
```
transaction = TokenMintTransaction(
    token_id=token_id,
    amount=amount,  # lowest denomination, must be positive and not zero
).freeze_with(client)

transaction.sign(operator_key)  
transaction.sign(supply_key)  
transaction.execute(client)
```
#### Method Chaining:
```
transaction = (
    TokenMintTransaction()
    .set_token_id(token_id)
    .set_amount(amount) # lowest denomination, must be positive and not zero
    .freeze_with(client)
)
transaction.sign(operator_key)  
transaction.sign(admin_key)  
transaction.execute(client)
```

### Minting a Non-Fungible Token

#### Pythonic Syntax:
```
transaction = TokenMintTransaction(
    token_id=token_id,
    metadata=metadata  # Bytes for non-fungible tokens (NFTs)
).freeze_with(client)

transaction.sign(operator_key)  
transaction.sign(supply_key)  
transaction.execute(client)
```
#### Method Chaining:
```
transaction = (
    TokenMintTransaction()
    .set_token_id(token_id)
    .set_metadata(metadata)  # Bytes for non-fungible tokens (NFTs)
    .freeze_with(client)
)
transaction.sign(operator_key)  
transaction.sign(admin_key)  
transaction.execute(client)
```

### Associating a Token

#### Pythonic Syntax:
```
transaction = TokenAssociateTransaction(
    account_id=recipient_id,
    token_ids=[token_id]
).freeze_with(client)

transaction.sign(recipient_key)
transaction.execute(client)
```
#### Method Chaining:
```
transaction = (
        TokenAssociateTransaction()
        .set_account_id(recipient_id)
        .add_token_id(token_id)
        .freeze_with(client)
        .sign(recipient_key)
    )

    transaction.execute(client)
```

### Dissociating a Token

#### Pythonic Syntax:
```
transaction = TokenDissociateTransaction(
    account_id=recipient_id,
    token_ids=[token_id]
).freeze_with(client)

transaction.sign(recipient_key)
transaction.execute(client)
```
#### Method Chaining:
```
transaction = (
        TokenDissociateTransaction()
        .set_account_id(recipient_id)
        .add_token_id(token_id)
        .freeze_with(client)
        .sign(recipient_key)
    )

    transaction.execute(client)
```

### Transferring Tokens

#### Pythonic Syntax:
```
transaction = TransferTransaction(
    token_transfers={
        token_id: {
            operator_id: -amount,  
            recipient_id: amount   
        }
    }
).freeze_with(client)

transaction.sign(operator_key)
transaction.execute(client)

```
#### Method Chaining:
```
    transaction = (
        TransferTransaction()
        .add_token_transfer(token_id, operator_id, -amount)
        .add_token_transfer(token_id, recipient_id, amount)
        .freeze_with(client)
        .sign(operator_key)
    )

    transaction.execute(client)
```

### Deleting a Token

#### Pythonic Syntax:
```
transaction = TokenDeleteTransaction(
    token_id=token_id
).freeze_with(client)

transaction.sign(admin_key)  # Admin key must have been set during token creation.
transaction.sign(operator_key)
transaction.execute(client)
```
#### Method Chaining:
```
    transaction = (
        TokenDeleteTransaction()
        .set_token_id(token_id)
        .freeze_with(client)
    )

    transaction.sign(admin_key) # Admin key must also have been set in Token Create
    transaction.sign(operator_key)
    transaction.execute(client)
```

### Freezing a Token

#### Pythonic Syntax:
```
transaction = TokenFreezeTransaction(
    token_id=token_id
    account_id=account_id
).freeze_with(client)

transaction.sign(freeze_key)  # Freeze key must have been set during token creation.
transaction.execute(client)
```
#### Method Chaining:
```
    transaction = (
        TokenFreezeTransaction()
        .set_token_id(token_id)
        .set_account_id(account_id)
        .freeze_with(client)
    )

    transaction.sign(freeze_key) # Freeze key must also have been set in Token Create
    transaction.execute(client)
```
### Unfreezing a Token

#### Pythonic Syntax:
```
transaction = TokenUnfreezeTransaction(
    token_id=token_id
).freeze_with(client)
transaction.sign(freeze_key)
transaction.execute(client)
```
#### Method Chaining:
```
transaction = (
        TokenUnfreezeTransaction()
        .set_token_id(token_id)
        .set_account_id(account_id)
        .freeze_with(client)
    )
    transaction.sign(freeze_key)
    transaction.execute(client)
```

### Transferring HBAR

#### Pythonic Syntax:
```
transaction = TransferTransaction(
    hbar_transfers={
        operator_id: -100000000,  # send 1 HBAR (in tinybars)
        recipient_id: 100000000
    }
).freeze_with(client)

transaction.sign(operator_key)
transaction.execute(client)
```
#### Method Chaining:
```
    transaction = (
        TransferTransaction()
        .add_hbar_transfer(operator_id, -100000000)  # send 1 HBAR (in tinybars)
        .add_hbar_transfer(recipient_id, 100000000)  
        .freeze_with(client)
    )

    transaction.sign(operator_key)
    transaction.execute(client)
```

### Creating a Topic

#### Pythonic Syntax:
```
    transaction = (
        TopicCreateTransaction(
            memo="My Super Topic Memo",
            admin_key=topic_admin_key)
        .freeze_with(client)
        .sign(operator_key)
    )

    transaction.execute(client)
```
#### Method Chaining:
```
transaction = (
    TopicCreateTransaction()
    .set_memo("My Super Topic Memo")
    .set_admin_key(topic_admin_key)
    .freeze_with(client)
)

transaction.sign(operator_key)
transaction.execute(client)
```

### Submitting a Topic Message

#### Pythonic Syntax:
```
transaction = (
    TopicMessageSubmitTransaction(topic_id=topic_id, message="Hello, from Python SDK!")
    .freeze_with(client)
    .sign(operator_key)
)

transaction.execute(client)

```
#### Method Chaining:
```
transaction = (
    TopicMessageSubmitTransaction()
    .set_topic_id(topic_id)
    .set_message("Hello, from Python SDK!")
    .freeze_with(client)
)

transaction.sign(operator_key)
transaction.execute(client)

```

### Updating a Topic

#### Pythonic Syntax:
```
transaction = (
    TopicUpdateTransaction(topic_id=topic_id, memo="Python SDK updated topic")
    .freeze_with(client)
    .sign(operator_key)
)

transaction.execute(client)
```
#### Method Chaining:
```
transaction = (
    TopicUpdateTransaction()
    .set_topic_id(topic_id)
    .set_memo("Python SDK updated topic")
    .freeze_with(client)
)

transaction.sign(operator_key)
transaction.execute(client)

```

### Deleting a Topic

#### Pythonic Syntax:
```
transaction = (
    TopicDeleteTransaction(topic_id=topic_id)
    .freeze_with(client)
    .sign(operator_key)
)
transaction.execute(client)
```
#### Method Chaining:
```
transaction = (
    TopicDeleteTransaction()
    .set_topic_id(topic_id)
    .freeze_with(client)
)

transaction.sign(operator_key)
transaction.execute(client)

```

### Querying Topic Info

#### Pythonic Syntax:
```
topic_info_query = TopicInfoQuery(topic_id=topic_id)
topic_info = topic_info_query.execute(client)
print(topic_info)

```
#### Method Chaining:
```
topic_info_query = (
    TopicInfoQuery()
    .set_topic_id(topic_id)
)

topic_info = topic_info_query.execute(client)
print(topic_info)

```

### Querying Topic Message

#### Pythonic Syntax:
```
query = TopicMessageQuery(
    topic_id=topic_id,
    start_time=datetime.utcnow(),
    chunking_enabled=True,
    limit=0
)

query.subscribe(client)

```
#### Method Chaining:
```
query = (
    TopicMessageQuery()
    .set_topic_id(topic_id) 
    .set_start_time(datetime.utcnow()) 
    .set_chunking_enabled(True) 
    .set_limit(0) 
    )

query.subscribe(client)
```

## Contributing

Contributions are welcome! Please follow these steps:

    1. Fork this repository.
    2. Create a new branch with your feature or fix.
    3. Make your changes and ensure the tests pass.
    3. Submit a pull request.

Please ensure all new code is covered by unit tests.

## License

This project is licensed under the MIT License.
