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

In this more advanced example, we are using imports to load env, to set up the client and network, and to form the Token Create Transaction and check the response:

```python
import sys
from dotenv import load_dotenv
from os import getenv

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.response_code import ResponseCode

# 1. Setup Client
load_dotenv()
operator_id = AccountId.from_string(getenv('OPERATOR_ID',''))
operator_key = PrivateKey.from_string(getenv('OPERATOR_KEY',''))

network = Network(getenv('NETWORK',''))
client = Client(network)
client.set_operator(operator_id, operator_key)

# 2. Build the transaction
create_tx = (
    TokenCreateTransaction()
    .set_token_name("Example Token")
    .set_token_symbol("EXT")
    .set_treasury_account_id(operator_id)
    .set_initial_supply(100000)
    .freeze_with(client)
    .sign(operator_key)
)

# 3. Execute and get receipt
receipt = create_tx.execute(client)

# 4. Validate Success
if receipt.status != ResponseCode.SUCCESS:
    print(f"Token creation on Hedera failed: {ResponseCode(receipt.status).name}")
    sys.exit(1)

# 5. Extract the Token ID
token_id = receipt.token_id
print(f"🎉 Created new token on the Hedera network with ID: {token_id}")
```

## Extra Support
It takes time to be familiar with where everything is located to import correctly. 

- For reference, look at the [examples](../../../../examples)
- For an explanation of the project structure read [project_structure.md](project_structure.md)
- Set up [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance) to help you spot errors in your import locations
