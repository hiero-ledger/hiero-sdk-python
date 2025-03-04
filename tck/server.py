import logging
from jsonrpcserver import serve
import utils, account_create

# NOTE: enable if you want to see the logs
logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    serve(port=8544)  # Specify your desired port here
