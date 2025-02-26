# Hiero Python SDK – Syntax Flexibility

The Hedera SDK in Python supports two distinct syntax styles for creating and executing transactions:

- Pythonic Syntax: Ideal for developers who prefer explicit constructor-style initialization.
- Method Chaining: Provides a fluent API style for chaining methods, commonly used in many SDKs.

You can choose either syntax or even mix both styles in your projects.


## Table of Contents

- [Account Transactions](#account-transactions)
  - [Creating an Account](#creating-an-account)
  - [Querying Account Balance](#querying-account-balance)
  - [Creating a Token](#creating-a-token)
- [Token Transactions](#token-transactions)
  - [Minting a Fungible Token](#minting-a-fungible-token)
  - [Minting a Non-Fungible Token](#minting-a-non-fungible-token)
  - [Associating a Token](#associating-a-token)
  - [Dissociating a Token](#dissociating-a-token)
  - [Transferring Tokens](#transferring-tokens)
  - [Deleting a Token](#deleting-a-token)
  - [Freezing a Token](#freezing-a-token)
- [HBAR Transactions](#hbar-transactions)
  - [Transferring HBAR](#transferring-hbar)
- [Topic Transactions](#topic-transactions)
  - [Creating a Topic](#creating-a-topic)
  - [Submitting a Topic Message](#submitting-a-topic-message)
  - [Updating a Topic](#updating-a-topic)
  - [Deleting a Topic](#deleting-a-topic)
  - [Querying Topic](#querying-topic)
  - [Querying Topic Message](#querying-topic-message)


## Account Transactions

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


## Token Transactions

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

## HBAR Transactions

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

## Topic Transactions

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