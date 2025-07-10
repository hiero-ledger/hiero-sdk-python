# Running Example Scripts

This guide will help you set up and run the example scripts in the /examples directory.

## 1. Create an `.env` File

- Navigate to the /examples directory:
  ```bash
  cd examples
  ```
- Create a new file named `.env` in this directory.

## 2. Sample Contents for `.env`

Paste the following template into your `.env` file:

```env
OPERATOR_ID=0.0.xxxxx
OPERATOR_KEY=302e020100300506032b6570... (your private key)
```

Replace the values with your actual operator account ID and private key.

## 3. How to Get Your Operator Account ID and Private Key (Testnet)

- Register for a Hedera testnet account at [portal.hedera.com](https://portal.hedera.com/register).
- Once registered and logged in, go to your testnet profile.
- Find your Account ID (looks like 0.0.xxxxx) and Private Key.
- Copy these values and paste them into your `.env` file as shown above.

**Keep your private key secure and never share it publicly.**

## 4. Running Example Scripts

- Ensure you are in the `/examples` directory and your `.env` file is present.
- Run an example script using Python 3:
  ```bash
  python3 example_script.py
  ```
  Replace example_script.py with the script you want to run.

---

For detailed syntax examples and API reference, see [README_syntax.md](README_syntax.md).