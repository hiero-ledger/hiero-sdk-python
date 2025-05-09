import os
from dotenv import load_dotenv
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenType
from hiero_sdk_python.logger.log_level import LogLevel
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction, TokenKeys, TokenParams

load_dotenv(override=True)

class IntegrationTestEnv:
    def __init__(self):
        network = Network(os.getenv('NETWORK'))
        self.client = Client(network)
        operator_id = os.getenv('OPERATOR_ID')
        operator_key = os.getenv('OPERATOR_KEY')
        if operator_id and operator_key:
            self.operator_id = AccountId.from_string(operator_id)
            self.operator_key = PrivateKey.from_string(operator_key)
            self.client.set_operator(self.operator_id, self.operator_key)
        
        self.client.logger.set_level(LogLevel.ERROR)
        self.public_operator_key = self.operator_key.public_key()
        
    def close(self):
        self.client.close()
    

def create_fungible_token(env):
    token_params = TokenParams(
            token_name="PTokenTest34",
            token_symbol="PTT34",
            decimals=2,
            initial_supply=1000,
            treasury_account_id=env.operator_id,
            token_type=TokenType.FUNGIBLE_COMMON,
            supply_type=SupplyType.FINITE,
            max_supply=10000
        )
    
    token_keys = TokenKeys(
            admin_key=env.operator_key,
            supply_key=env.operator_key,
            freeze_key=env.operator_key,
            wipe_key=env.operator_key
        )
        
    token_transaction = TokenCreateTransaction(token_params, token_keys)
    token_transaction.freeze_with(env.client)
    token_receipt = token_transaction.execute(env.client)
    
    assert token_receipt.status == ResponseCode.SUCCESS, f"Token creation failed with status: {ResponseCode.get_name(token_receipt.status)}"
    
    return token_receipt.tokenId

def create_nft_token(env):
    token_params = TokenParams(
        token_name="PythonNFTToken",
        token_symbol="PNFT",
        decimals=0,
        initial_supply=0,
        treasury_account_id=env.operator_id,
        token_type=TokenType.NON_FUNGIBLE_UNIQUE,
        supply_type=SupplyType.FINITE,
        max_supply=10000  
    )
    
    token_keys = TokenKeys(
        admin_key=env.operator_key,
        supply_key=env.operator_key,
        freeze_key=env.operator_key
    )

    transaction = TokenCreateTransaction(token_params, token_keys)
    transaction.freeze_with(env.client)
    token_receipt = transaction.execute(env.client)
    
    assert token_receipt.status == ResponseCode.SUCCESS, f"Token creation failed with status: {ResponseCode.get_name(token_receipt.status)}"
    
    return token_receipt.tokenId