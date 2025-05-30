import os

from dotenv import load_dotenv
from dataclasses import dataclass

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
# from hiero_sdk_python.query.token_info_query import TokenInfoQuery

from hiero_sdk_python.client.client import Client
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenType
from hiero_sdk_python.logger.log_level import LogLevel
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction, TokenKeys, TokenParams
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_pause_transaction import TokenPauseTransaction
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from hiero_sdk_python.hbar                    import Hbar

load_dotenv(override=True)

_NO_KEY = object()   # unique sentinel meaning “no key argument was provided”

@dataclass
class Account:
    id:    AccountId
    key:   PrivateKey

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

    def freeze_sign_execute(self, tx, *signing_keys):
        """Freeze, sign with provided keys (or operator), execute, and assert success."""
        # Freeze
        tx = tx.freeze_with(self.client)
        # Sign (default to operator_key if none provided)
        for key in signing_keys or (self.operator_key,):
            tx = tx.sign(key)
        # Execute and assert success
        receipt = tx.execute(self.client)
        assert receipt.status == ResponseCode.SUCCESS, (
            f"Transaction failed: {ResponseCode.get_name(receipt.status)}"
        )
        return receipt

    def create_account(self, initial_hbar: float = 1.0) -> Account:
        """Create a new account funded with `initial_hbar` HBAR, defaulting to 1."""
        key     = PrivateKey.generate()
        receipt = self.freeze_sign_execute(
            AccountCreateTransaction()
                .set_key(key.public_key())
                .set_initial_balance(Hbar(initial_hbar)),
            self.operator_key,
        )
        return Account(id=receipt.accountId, key=key)
    
    def associate_and_transfer(self, receiver: AccountId, receiver_key, token_id, amount: int):
        """Associate the token id for the receiver account. Then transfer an amount of the token from the operator (sender) to the receiver."""
        self.freeze_sign_execute(
            TokenAssociateTransaction()
                .set_account_id(receiver)
                .add_token_id(token_id),
            receiver_key,
        )
        self.freeze_sign_execute(
            TransferTransaction()
                .add_token_transfer(token_id,    self.operator_id, -amount)
                .add_token_transfer(token_id,    receiver,          amount),
            self.operator_key,
        )

    def pause_token(self, token_id, key=_NO_KEY):
            """
            Pause a token with explicit control over which key (if any) is used to sign.
            Allows for multiple testing scenarios:
            1. Default (key=_NO_KEY):  
                Use the operator’s pause key to sign and submit.

            2. Explicit no-key (key=None)

            3. Custom key (key=some PrivateKey):  
                • E.g. a randomly generated key different to the pause key
                • The operator’s key again on an already-paused token
            """
            tx = TokenPauseTransaction().set_token_id(token_id)
            tx = tx.freeze_with(self.client)

            if key is _NO_KEY:
                # happy-path: operator’s pause key
                tx = tx.sign(self.operator_key)
            elif key is not None:
                # custom key provided
                tx = tx.sign(key)
            # else key is None → leave unsigned

            return tx.execute(self.client)

    def get_balance(self, account_id: AccountId):
        """
        Wraps:
          balance = CryptoGetAccountBalanceQuery(account_id).execute(self.client)
        """
        return CryptoGetAccountBalanceQuery(account_id).execute(self.client)

    def get_token_info(self, token_id):
        """
        Wraps:
          info = TokenInfoQuery().set_token_id(token_id).execute(self.client)
        """
        return TokenInfoQuery().set_token_id(token_id).execute(self.client)
    
def create_fungible_token(env, opts=[]):
    """
    Create a fungible token with the given options.

    Args:
        env: The environment object containing the client and operator account.
        opts: List of optional functions that can modify the token creation transaction before execution.
             Example opt function:
             lambda tx: tx.set_treasury_account_id(custom_treasury_id).freeze_with(client)
    """
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
            # pause_key=  None  # implicitly “no pause key” use opts to add one
        )
        
    token_transaction = TokenCreateTransaction(token_params, token_keys)
    
    # Apply optional functions to the token creation transaction
    for opt in opts:
        opt(token_transaction)
    
    token_receipt = token_transaction.execute(env.client)
    
    assert token_receipt.status == ResponseCode.SUCCESS, f"Token creation failed with status: {ResponseCode.get_name(token_receipt.status)}"
    
    return token_receipt.tokenId

def create_nft_token(env, opts=[]):
    """
    Create a non-fungible token (NFT) with the given options.

    Args:
        env: The environment object containing the client and operator account.
        opts: List of optional functions that can modify the token creation transaction before execution.
             Example opt function:
             lambda tx: tx.set_treasury_account_id(custom_treasury_id).freeze_with(client)
    """
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
        # pause_key=  None  # implicitly “no pause key” use opts to add one

    )

    transaction = TokenCreateTransaction(token_params, token_keys)

    # Apply optional functions to the token creation transaction
    for opt in opts:
        opt(transaction)

    token_receipt = transaction.execute(env.client)
    
    assert token_receipt.status == ResponseCode.SUCCESS, f"Token creation failed with status: {ResponseCode.get_name(token_receipt.status)}"
    
    return token_receipt.tokenId