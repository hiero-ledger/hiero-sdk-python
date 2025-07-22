from hiero_sdk_python.file.file_info_query import FileInfoQuery
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python import (
    AccountId,
    PrivateKey,
    Network,
    Client,
    ResponseCode,
    Hbar 
)
import os
from dotenv import load_dotenv
load_dotenv()

network = Network(network='testnet')
client = Client(network)
account_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
private_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))
client.set_operator(account_id, private_key)

invalid_file_id = FileId("0.0.999999999")
query = FileInfoQuery().set_file_id(invalid_file_id)

# bypass automatic cost query
query.set_query_payment(Hbar(1)) 

try:
    result = query.execute(client)
except PrecheckError as e:
    print(f"Error code: {e.status} ({ResponseCode(e.status).name})")
    if e.status == ResponseCode.INVALID_FILE_ID:
        print("Success: Received the expected INVALID_FILE_ID error.")
    else:
        print(f"Failure: Received an unexpected error.")