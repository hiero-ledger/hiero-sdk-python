import os
from dotenv import load_dotenv
from hedera import (
    Client,
    AccountId,
    PrivateKey,
    TransactionId
)

# Load .env file
load_dotenv()

def setup_client() -> Client:
    # Initialize and set up the client with operator account.
    
    try:
        operator_id = AccountId.fromString(os.environ["OPERATOR_ID"])
        operator_key = PrivateKey.fromString(os.environ["OPERATOR_KEY"])
        network_name = os.environ.get("NETWORK", "testnet") 
    except KeyError as e:
        raise Exception("Environment variable {} must be set.".format(e))

    print("Initializing client for {}...".format(network_name))
    
    client = Client.forName(network_name)
    client.setOperator(operator_id, operator_key)

    print("Client setup complete.")
    return client

def print_channel_info(channel):
    # Print token service methods available on the gRPC channel.
    print("\n--- Channel Info ---")
    print("Channel object:", type(channel))
    print("Token stub methods available:")
    for method in dir(channel.token):
        if not method.startswith("__"):
            print(" →", method)

def print_network_info(client: Client):
    # Print operator account and network nodes.
    print("\nNetwork Info")
    print("Operator Account ID: {}".format(client.operatorAccountId))
    
    node_ids = client.network.getNodeAccountIds()
    print("Network contains {} nodes:".format(len(node_ids)))
    for i, node_id in enumerate(node_ids):
        print("  Node {}: {}".format(i, node_id))

def print_transaction_info(client: Client):
    # Generate and print a transaction ID.
    print("\nTransaction Info")
    
    tx_id = TransactionId.generate(client.operatorAccountId)
    
    print("Generated Transaction ID: {}".format(tx_id))
    print("  → For Account ID: {}".format(tx_id.accountId))
    print("  → Valid Start Time: {}".format(tx_id.validStart))
    return tx_id

def main():
    # Main function to run the example
    print("Starting client.py example")
    
    client = setup_client()
    
    node = client.network.current_node
    channel = node._get_channel()
    
    print_channel_info(channel)
    print_network_info(client)
    tx_id = print_transaction_info(client)
    
    client.close()
    print("\nExample complete")

if __name__ == "__main__":
    main()