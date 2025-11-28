## Setup Network and Client

All transactions and queries on the Hedera network require a network and client set-up.

To do this you'll need to import the relevant functionality, variables from .env and attach them to the Network and Client classes as appropriate.

### Worked Example
```python
from dotenv import load_dotenv
from os import getenv

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.client.network import Network

# Load the network name, the operator id and key strings from .env
load_dotenv()
network_name = getenv('NETWORK','')
operator_id_string = getenv('OPERATOR_ID','')
operator_key_string = getenv('OPERATOR_KEY','')

# Convert operator id and key strings into AccountId and PrivateKey as Client requires those types
operator_id = AccountId.from_string(operator_id_string)
operator_key = PrivateKey.from_string(operator_key_string)

# Set the Network
network = Network(network_name)
# Set the Client on that Network
client = Client(network)
# Set the credentials for the Client
client.set_operator(operator_id, operator_key)

print(f"Connected to Hedera {network_name} as operator {client.operator_account_id}")
```

### Extra Support
Read about Network and Client in more detail [here](docs/sdk_developers/training/network_and_client.md)
