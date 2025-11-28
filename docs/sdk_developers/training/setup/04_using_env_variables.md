## Loading Credentials Into Scripts

Your credentials stored at .env are required to run transactions on Hedera testnet.

- dotenv has load_dotenv() to load credentails
- os has getenv() to read the credentials

We use both, for example:

```python
# Import dotenv and os 
from dotenv import load_dotenv
from os import getenv

# Load variables from .env into environment
load_dotenv()

# Read the variables
operator_id_string = getenv('OPERATOR_ID')
operator_key_string = getenv('OPERATOR_KEY')

# Printing confirming loading and reading
print(f"Congratulations! We loaded your operator ID: {operator_id_string}.")
print("Your operator key was loaded successfully (not printed for security).")

```

