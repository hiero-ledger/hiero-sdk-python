import logging
import utils
import account_create
from jsonrpcserver import serve, method

# NOTE: enable if you want to see the logs
# logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    serve(port=8545)  # Specify your desired port here
