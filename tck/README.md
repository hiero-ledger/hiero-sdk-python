# Testing Compatibility Kit (TCK) Guide

This document describes how to run Hiero TCK tests for the Python SDK.
## Setup
1. **Set up the Python SDK**

    Follow the steps in the [Hiero TCK README](https://github.com/hiero-ledger/hiero-sdk-tck) to set up the tck to test this sdk against.
    Use Docker setup for easy setup and management. 

## Running the TCK Tests

1. **Navigate to the TCK Directory in the Python SDK**

   Change directories to the SDKs JSON-RPC server

```shell script
cd hiero-python-sdk/tck
```

2. **Start the SDK testing Server**

   Launch the SDK testing server by running:

```shell script
python3 server.py
```

3. **Execute TCK Tests**

   With the SDK server running, you can now execute tests from the tck directly or from docker. Refer to the TCK's README for more information.


## Troubleshooting

- **Environment Variables Not Set Correctly:**  
  Double-check your `.env` files for typos or mismatched variables between the TCK and Python SDK.

- **Server Issues:**  
  Ensure no other application is using the port required by the TCK server. Check server logs for further details if the server does not start as expected.

- **Test Failures:**  
  Review the output for any error messages. They can give insights into configuration issues or missing dependencies.

- **Enable Logging:**
  In the server.py file, uncomment `logging.basicConfig(level=logging.DEBUG)` to enable logging, and better debug what is happening.

## Contributing
Follow these steps established by the account_create.py:

1. Create a new method and annotate it with @method
2. Read the TCK documentation to understand which SDK methods/classes to call
3. Return a success if no errors exist, and the method successfully executes.

