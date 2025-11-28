## Lab: Setup

In this lab, you'll set up a Network and Client instance and run an account balance query on the Hedera network.

## Step 1: Create a file at /examples/lab1.py
Create a lab1 practice file and add a main function:
```python
def main():
    # Placeholder to call functions

if __name__ == "__main__":
    main()
```
You'll be running this by: "uv run /examples/practice.py"

## Step 2: Create a function: set_up_network_and_client
In this function be sure to:
- Import required packages
- Load OPERATOR_ID as operator_id_string, OPERATOR_KEY as operator_key_string
- Connect to Hedera testnet
- Connect your credentials to the Client

Note: Check it works by running the file at "uv run /examples/practice.py"
```python
def set_up_network_and_client():
    # Placeholder to set up network and client

def main():
    # Call the function and return any needed variables
    set_up_network_and_client()

if __name__ == "__main__":
    main()
```

## Step 3: Create query_account_balance
- Pass in the client and operator_key
- Perform an account balance query
- Print the hbar balance
- Print the token balance
- Call this from main()

Syntax:
```python
    balance = CryptoGetAccountBalanceQuery(operator_id).execute(client)
    print(f" Hbar balance is {balance.hbars}")
    print(f" Token balance is {balance.token_balances}")
```

Your main will now look more like this:
```python
def main():
    client, operator_id = set_up_network_and_client()
    query_account_balance(client, operator_id)

if __name__ == "__main__":
    main()
```

Check it all works by running it "uv run /examples/practice.py"


#### Solution: WARNING!

```python
from dotenv import load_dotenv
from os import getenv
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery

def set_up_network_and_client():
    load_dotenv()

    network_name = getenv('NETWORK','')
    network = Network(network_name)
    client = Client(network)

    operator_id_string = getenv('OPERATOR_ID','')
    operator_key_string = getenv('OPERATOR_KEY','')

    operator_id = AccountId.from_string(operator_id_string)
    operator_key = PrivateKey.from_string(operator_key_string)

    client.set_operator(operator_id, operator_key)
    print(f"Connected to Hedera {network_name} as operator {client.operator_account_id}")
    return client, operator_id

def query_account_balance(client, operator_id):
    balance = CryptoGetAccountBalanceQuery(operator_id).execute(client)
    print(f" Hbar balance is {balance.hbars}")
    print(f" Token balance is {balance.token_balances}")

def main():
    client, operator_id = set_up_network_and_client()
    query_account_balance(client, operator_id)

if __name__ == "__main__":
    main()
```