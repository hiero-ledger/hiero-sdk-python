# Introduction to Hedera Network and Client

## Introduction

Before creating any transactions or querying the Hedera blockchain, every developer must understand two foundational concepts: **Network** and **Client**.

- The **Network** is your gateway to the Hedera nodes—the servers that process transactions and maintain the ledger.
- The **Client** is your interface that connects your application to the network using your operator credentials.

Without properly setting up both, you cannot interact with Hedera at all. This guide covers these essentials before any transaction logic.

## Contents

- [What is a Network?](#what-is-a-network)
  - [Hedera Networks](#hedera-networks)
  - [What are Nodes?](#what-are-nodes)
  - [Example: Network Dictionary](#example-network-dictionary)
  - [Mirror Nodes](#mirror-nodes)
- [What is a Client?](#what-is-a-client)
  - [Client Responsibilities](#client-responsibilities)
  - [Simple Client Diagram](#simple-client-diagram)
- [Setting Up a Client](#setting-up-a-client)
  - [Step 1: Initialize a Network Instance](#step-1-initialize-a-network-instance)
  - [Step 2: Initialize the Client and Set Operator Account](#step-2-initialize-the-client-and-set-operator-account)
  - [Checking Operator Status](#checking-operator-status)
- [Client Capabilities](#client-capabilities)
  - [1. Node Selection](#1-node-selection)
  - [2. Mirror Node Access](#2-mirror-node-access)
  - [3. Transaction ID Generation](#3-transaction-id-generation)
  - [4. Retry Configuration](#4-retry-configuration)
  - [5. Logging](#5-logging)
- [How Network and Client Work Together](#how-network-and-client-work-together)
  - [The Interaction Flow](#the-interaction-flow)
  - [Example: Complete Setup](#example-complete-setup)
- [Resource Management](#resource-management)
  - [Manual Cleanup](#manual-cleanup)
  - [Automatic Cleanup with Context Manager](#automatic-cleanup-with-context-manager)
- [Summary](#summary)

---

## What is a Network?

A **Network** is a collection of Hedera nodes that process transactions, maintain consensus, and validate the distributed ledger. Each network has its own independent ledger state and accounts.

### Hedera Networks

Hedera provides multiple networks for different purposes:

| Network        | Purpose                      | Real HBAR | Use Case                            |
| -------------- | ---------------------------- | --------- | ----------------------------------- |
| **mainnet**    | Live production network      | Yes       | Real transactions with actual value |
| **testnet**    | Public sandbox               | No        | Testing without spending real HBAR  |
| **previewnet** | Early access to new features | No        | Testing upcoming mainnet changes    |
| **solo**       | Local private network        | No        | Local development and debugging     |

### What are Nodes?

**Nodes** are servers that validate transactions, maintain the ledger, and respond to queries. Each node is identified by:

- **Account ID**: A unique identifier (e.g., `0.0.3`, `0.0.4`) that represents the node on the network
- **Address**: The network address and port (e.g., `0.testnet.hedera.com:50211`)

Your client communicates with these nodes when sending transactions or queries. Multiple nodes provide redundancy and failover capability.

### Example: Network Dictionary

A network's node configuration is essentially a mapping of node account IDs to their addresses:

```python
# Simplified example of testnet nodes
testnet_nodes = {
    "0.0.3": "0.testnet.hedera.com:50211",
    "0.0.4": "1.testnet.hedera.com:50211",
    "0.0.5": "2.testnet.hedera.com:50211",
    "0.0.6": "3.testnet.hedera.com:50211",
}
```

The Hedera SDK provides **default node configurations** for each official network, so you don't need to manually specify every node. However, you can customize this if needed.

### Mirror Nodes

In addition to regular nodes, Hedera has **mirror nodes**. Mirror nodes provide:

- REST API access for querying historical data
- gRPC streaming subscriptions for topics and contract events
- Read-only access without needing operator credentials

Each network has its default mirror node:

| Network    | Mirror Node URL                                |
| ---------- | ---------------------------------------------- |
| mainnet    | `https://mainnet-public.mirrornode.hedera.com` |
| testnet    | `https://testnet.mirrornode.hedera.com`        |
| previewnet | `https://previewnet.mirrornode.hedera.com`     |
| solo       | `http://localhost:5551`                        |

---

## What is a Client?

A **Client** is the main interface your application uses to interact with the Hedera network. It manages:

- **Network connection**: Maintains links to nodes and mirror nodes
- **Operator credentials**: Stores your account ID and private key for authentication
- **Node selection**: Chooses which node to send requests to (automatically using round-robin)
- **Mirror access**: Provides gRPC channels to mirror nodes for subscriptions
- **Transaction ID generation**: Creates unique transaction IDs for tracking
- **Retry logic**: Handles failed requests with automatic retries
- **Logging**: Tracks network interactions for debugging

### Client Responsibilities

Think of the Client as a librarian that:

1. Knows all the libraries (nodes) in your city (network)
2. Knows who you are (operator credentials)
3. Can send you to the nearest available library (node selection)
4. Can help you find books (queries) or place orders (transactions)
5. Remembers all your interactions (logging)

### Simple Client Diagram

```
┌────────────────────────────────────────────────┐
│         Your Application Code                  │
└────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────┐
│              Client Instance                   │
├────────────────────────────────────────────────┤
│ • Network configuration (nodes & mirror)       │
│ • Operator Account ID                          │
│ • Operator Private Key                         │
│ • gRPC channels to nodes                       │
│ • Mirror node gRPC channel                     │
│ • Retry configuration (max_attempts=10)        │
└────────────────────────────────────────────────┘
                      ↓
        ┌─────────────┴──────────────┐
        ↓                            ↓
   ┌─────────────┐          ┌───────────────┐
   │ Hedera Nodes│          │ Mirror Nodes  │
   │ (gRPC)      │          │ (gRPC)        │
   └─────────────┘          └───────────────┘
```

---

## Setting Up a Client

Setting up a client involves two main steps:

1. **Create a Network instance** to configure which Hedera network to connect to
2. **Create a Client instance** and set your operator credentials

### Step 1: Initialize a Network Instance

Create a Network by specifying which Hedera network you want to use:

```python
from hiero_sdk_python.client.network import Network

# Connect to testnet (the default)
network = Network("testnet")

# Or connect to other networks
network_mainnet = Network("mainnet")
network_preview = Network("previewnet")
network_solo = Network("solo")

print(f"Network name: {network.network}")
print(f"Mirror address: {network.get_mirror_address()}")
print(f"Number of nodes: {len(network.nodes)}")
```

**What happens during Network initialization:**

1. The Network name is set (e.g., "testnet")
2. Default nodes are loaded for that network
3. The mirror node address is configured
4. One node is randomly selected as the current node
5. The ledger ID is set (this identifies the network's ledger)

**Customizing the Network:**

If you need custom nodes, you can provide them:

```python
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.node import _Node
from hiero_sdk_python.account.account_id import AccountId

# Create custom nodes
custom_nodes = [
    _Node(AccountId(0, 0, 3), "my-node-1.example.com:50211", None),
    _Node(AccountId(0, 0, 4), "my-node-2.example.com:50211", None),
]

# Initialize network with custom nodes
custom_network = Network("custom", nodes=custom_nodes)
```

### Step 2: Initialize the Client and Set Operator Account

Now create a Client instance and configure your operator credentials:

```python
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
import os
from dotenv import load_dotenv

load_dotenv()

network = Network("testnet")
client = Client(network)

operator_id = AccountId.from_string(os.getenv("OPERATOR_ID"))
operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY"))

client.set_operator(operator_id, operator_key)
```

For a complete example, see [`examples/client/client.py`](../../../examples/client/client.py).

**Environment Variables:**

Store your credentials in a `.env` file (never commit to version control):

```bash
OPERATOR_ID=0.0.1001
OPERATOR_KEY=302e020100300506032b6570042204201234567890abcdef...
NETWORK=testnet
```

The `dotenv` library automatically loads these into Python's environment.

### Checking Operator Status

You can verify that the operator is correctly set:

```python
# Check if operator is set
if client.operator:
    print(f"Operator is configured: {client.operator.account_id}")
else:
    print("No operator configured yet")
```

---

## Client Capabilities

Once properly initialized and configured, the Client provides several capabilities:

### 1. Node Selection

The Client uses **round-robin node selection** to distribute requests across available nodes:

```python
# Get all available node account IDs
node_ids = client.get_node_account_ids()
print(f"Available nodes: {node_ids}")

# The current selected node
print(f"Current node: {client.network.current_node}")

# Each request automatically rotates to the next node
# You don't manually select nodes in most cases
```

**How node selection works:**

- Each time a request is made, the Client rotates to the next node
- When it reaches the last node, it wraps back to the first node
- This ensures load balancing across all available nodes

### 2. Mirror Node Access

The Client maintains a gRPC channel to the mirror node for subscriptions:

```python
# The mirror channel is automatically initialized
print(f"Mirror channel: {client.mirror_channel}")
print(f"Mirror stub: {client.mirror_stub}")

# This is used for subscribing to topics and contract events
# (We'll cover this in advanced guides)
```

### 3. Transaction ID Generation

Even without executing a transaction, you can generate transaction IDs using the Client:

```python
# Generate a unique transaction ID
transaction_id = client.generate_transaction_id()
print(f"Generated transaction ID: {transaction_id}")

# This requires that the operator account ID is set
```

A transaction ID consists of:

- The operator's account ID
- A unique timestamp
- It uniquely identifies the transaction on the network

### 4. Retry Configuration

The Client comes with automatic retry logic:

```python
# The default maximum attempts
print(f"Max retry attempts: {client.max_attempts}")

# This means if a request fails, the Client will retry up to 10 times
# before giving up
```

### 5. Logging

The Client includes a logger for debugging network interactions:

```python
# The Client automatically initializes a logger
logger = client.logger
print(f"Logger: {logger}")

# Logs are output based on the LOG_LEVEL environment variable
```

---

## How Network and Client Work Together

The Network and Client are separate but interdependent:

```
┌──────────────────────────────────────────────────────────────┐
│                  Your Application                            │
└──────────────────────────────────────────────────────────────┘
                           ↓
                    ┌──────────────┐
                    │   Client     │
                    └──────────────┘
                    ↙              ↘
          ┌─────────────────┐    ┌─────────────────┐
          │    Network      │    │ Operator        │
          ├─────────────────┤    │ Credentials     │
          │ • Nodes list    │    │ • Account ID    │
          │ • Mirror node   │    │ • Private Key   │
          │ • Ledger ID     │    └─────────────────┘
          └─────────────────┘
                    ↓
        ┌───────────────────────────┐
        │  Hedera Network           │
        ├───────────────────────────┤
        │ • Node 1 (0.0.3)          │
        │ • Node 2 (0.0.4)          │
        │ • Node 3 (0.0.5)          │
        │ • Mirror Node             │
        └───────────────────────────┘
```

### The Interaction Flow

1. **Network defines WHERE**: The Network specifies which servers (nodes) and mirror nodes exist and how to reach them
2. **Client provides WHO and HOW**: The Client specifies who you are (operator credentials) and manages the actual communication
3. **Together they enable communication**: The combination allows your application to securely interact with the Hedera blockchain

## -### Example: Complete Setup

-```python
+### Example: Complete Setup

```python
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
import os

# Create the network configuration
network = Network("testnet")
print(f"Connected to: {network.network}")
print(f"Nodes available: {len(network.nodes)}")

# Create the client with the network
client = Client(network)
print(f"Client initialized with network: {client.network.network}")

# Configure operator credentials
operator_id = AccountId.from_string(os.getenv("OPERATOR_ID"))
operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY"))

client.set_operator(operator_id, operator_key)
print(f"Operator set: {client.operator_account_id}")

# Now the client is ready for transactions
# (Though we're not executing any transactions in this guide)

print(f"Client is ready to use!")
print(f"Current node: {client.network.current_node._account_id}")
print(f"Mirror address: {client.network.get_mirror_address()}")

# Clean up when done
client.close()
```

---

## Resource Management

The Client maintains gRPC channels that should be properly closed when done:

### Manual Cleanup

```python
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.client.client import Client

network = Network("testnet")
client = Client(network)

# ... use client ...

# Close channels when done
client.close()
```

### Automatic Cleanup with Context Manager

Use Python's `with` statement for automatic cleanup:

```python
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.client.client import Client

network = Network("testnet")

with Client(network) as client:
    # Use the client
    print(f"Client is ready: {client.operator_account_id}")
    # Channels are automatically closed when exiting the block
```

This is the recommended approach for production code.

---

## Summary

### Key Takeaways

**Network:**

- Defines the Hedera network to connect to (mainnet, testnet, previewnet, solo)
- Contains a list of node servers with their addresses and account IDs
- Includes mirror node configuration for read-only access
- Handles automatic node discovery and fallback mechanisms

**Client:**

- Your main interface to the Hedera network
- Stores operator credentials (account ID and private key)
- Manages connections to nodes via gRPC
- Handles node selection using round-robin rotation
- Provides mirror node access for subscriptions
- Generates transaction IDs for tracking
- Includes retry logic for failed requests

**Together:**

- Network = WHERE to connect (the nodes)
- Client = WHO connects and HOW to connect (credentials and communication)
- You must properly set up both before any Hedera interaction

### Before Moving Forward

Before learning about transactions, queries, or other features, ensure you:

1. ✓ Understand what a Network is and its role
2. ✓ Understand what a Client is and its responsibilities
3. ✓ Can create a Network instance for your target Hedera network
4. ✓ Can create a Client instance and set operator credentials
5. ✓ Know how to use environment variables for credentials (never hardcode!)
6. ✓ Can properly close Client channels when done

---

## Next Steps

You can also explore the following stand-alone example script:

- `examples/client/client.py` – Complete network and client setup example with detailed logging.

Now that you understand Network and Client setup, you're ready to:

- **Create and submit transactions** to the Hedera network
- **Query the network** for account and transaction information
- **Subscribe to topics** via mirror nodes
- **Build complete Hedera applications**

The Network and Client are foundational—master them first!
