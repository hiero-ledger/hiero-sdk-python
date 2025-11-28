## Importing Functionality To Use In Scripts

Import all modules, classes and types required for your transaction to work by specifying their exact path after src/.

### Example: Importing TokenCreateTransactionClass
TokenCreateTransaction class is located inside src/hiero_sdk_python/tokens/token_create_transaction.py:

Therefore:
```python
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
```

### Example: Importing token_create_transaction.py
token_create_transaction.py is located at src/hiero_sdk_python/tokens.py:

Therefore:
```python
from hiero_sdk_python.tokens import token_create_transaction
```

### Advanced Example
You'll need to import everything you require. 

In this more advanced example, we are using: sys, TokenCreateTransaction, Client and ResponseCode.
```python
import sys
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.client import client
from hiero_sdk_python.response_code import ResponseCode

# 1. Build the transaction
create_tx = (
    TokenCreateTransaction()
    .set_token_name("Example Token")
    .set_token_symbol("EXT")
    .set_treasury_account_id(operator_id)
    .freeze_with(client)
    .sign(operator_key)
)

# 2. Execute and get receipt
receipt = create_tx.execute(client)

# 3. Validate Success
if receipt.status != ResponseCode.SUCCESS:
    print(f"Token creation on Hedera failed: {ResponseCode(receipt.status).name}")
    sys.exit(1)

# 4. Extract the Token ID
token_id = receipt.token_id
print(f"🎉 Created new token on the Hedera network with ID: {token_id}")
```

## Extra Support
It takes time to be familiar with where everything is located to import correctly. 

- For reference, look at the [examples](examples/) 
- For an explanation of the project structure read [project_structure.md](docs/sdk_developers/project_structure.md).
- Set up [Pylance](docs/sdk_developers/pylance.md) to help you spot errors in your import locations
