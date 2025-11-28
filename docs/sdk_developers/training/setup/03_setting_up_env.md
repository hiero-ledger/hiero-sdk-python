## Quick Start Env

### 1. Create Testnet Account

Create a testnet Hedera Portal account [here](https://portal.hedera.com/dashboard).

### 2. Create .env
Create a file named `.env` in your project root.

Add, ignoring the < > and without any quotation marks:

```bash
OPERATOR_ID=<YOUR_OPERATOR_ID> #your account id
OPERATOR_KEY=<YOUR_PRIVATE_KEY> #your testnet private key (can be ECDSA, ED25519 or DER)
NETWORK=testnet
```

For example:
```bash
OPERATOR_ID=0.0.1000000
OPERATOR_KEY=123456789
NETWORK=testnet
```

We have added `.env` to `.gitignore` to help ensure its never committed.


