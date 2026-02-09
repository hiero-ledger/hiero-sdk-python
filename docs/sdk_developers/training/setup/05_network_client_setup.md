## Setup Network and Client

All transactions and queries on the Hedera network require a network and client set-up.

To do this you'll need to import the relevant functionality, variables from .env and attach them to the Network and Client classes as appropriate.

### Worked Example
```python
import sys
from dotenv import load_dotenv
from os import getenv

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.client import client
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

### Extra Support
Read about Network and Client in more detail [here](../network_and_client.md)
