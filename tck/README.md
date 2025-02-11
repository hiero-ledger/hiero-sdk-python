# Testing Compatibility Toolkit (TCK) Guide

This document describes how to run Hiero TCK tests for the Python SDK.
## Setup
1. **Set up the Python SDK**

    Follow the steps in the [Hiero TCK README](https://github.com/hiero-ledger/hiero-sdk-tck) to clone the repository and set it up on your local machine.


2. **Environment Variables**

    Ensure that the environment variables in the `.env` file for both the TCK and the Python SDK are identical, to make sure that they run in the same configuration. 

## Running the TCK Tests

1. **Navigate to the TCK Directory in the Python SDK**

   Change directory to the location of the TCK within the Python SDK. For example:

```shell script
cd hiero-python-sdk/tck
```

2. **Start the TCK Server**

   Launch the TCK server by running:

```shell script
python3 server.py
```

3. **Execute TCK Tests**

   With the TCK server running, you can now execute tests either from the command line or directly via your IDE. Refer to the TCK's README for more information.


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

Contributions are welcome! Please follow these steps:

    1. Fork this repository.
    2. Create a new branch with your feature or fix.
    3. Make your changes and ensure the tests pass.
    3. Submit a pull request.

Please ensure all new code is covered by unit tests.

## License

This project is licensed under the MIT License.
