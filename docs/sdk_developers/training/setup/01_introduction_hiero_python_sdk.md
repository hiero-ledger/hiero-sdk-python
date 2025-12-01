## What is the Hiero Python SDK?

The Hiero Python SDK enables developers to use Python to interact with the Hedera Blockchain/DLT Network. 

For example, the Hiero Python SDK lets you:
- Create a token on the Hedera network
- Transfer Hbars between accounts
- Mint NFTs
- Create smart contracts

All using python code.

For example:
```python
create_tx = (
    TokenCreateTransaction()
    .set_token_name("Example Token")
    .set_token_symbol("EXT")
    .set_treasury_account_id(operator_id)
    .freeze_with(client)
    .sign(operator_key)
    .execute(client)
)

token_id = create_tx.token_id
print(f"🎉 Created a new token on the Hedera network with ID: {token_id}")
```

