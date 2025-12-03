import os
from pytest import fixture
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.logger.log_level import LogLevel
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction, TokenKeys, TokenParams
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from hiero_sdk_python.hbar                    import Hbar

load_dotenv(override=True)

@fixture
def env():
    """Integration test environment with client/operator set up."""
    e = IntegrationTestEnv()
    yield e
    e.close()

@dataclass
class Account:
    id:    AccountId
    key:   PrivateKey

class IntegrationTestEnv:

    def __init__(self) -> None:
        network = Network(os.getenv('NETWORK'))
        self.client = Client(network)
        self.operator_id: Optional[AccountId] = None
        self.operator_key: Optional[PrivateKey] = None
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

    def create_account(self, initial_hbar: float = 1.0) -> Account:
        """Create a new account funded with `initial_hbar` HBAR, defaulting to 1."""
        key = PrivateKey.generate()
        tx = (
            AccountCreateTransaction()
                .set_key(key.public_key())
                .set_initial_balance(Hbar(initial_hbar))
        )
        receipt = tx.execute(self.client)
        if receipt.status != ResponseCode.SUCCESS:
            raise AssertionError(
                f"Account creation failed: {ResponseCode(receipt.status).name}"
            )
        return Account(id=receipt.account_id, key=key)

    def associate_and_transfer(self, receiver: AccountId, receiver_key: PrivateKey, token_id, amount: int):
        """
        Associate the token with `receiver`, then transfer `amount` of the token
        from the operator to that receiver.
        """
        assoc_receipt = (
            TokenAssociateTransaction()
                .set_account_id(receiver)
                .add_token_id(token_id)
                .freeze_with(self.client)
                .sign(receiver_key)
                .execute(self.client)
        )
        if assoc_receipt.status != ResponseCode.SUCCESS:
            raise AssertionError(
                f"Association failed: {ResponseCode(assoc_receipt.status).name}"
            )

        transfer_receipt = (
            TransferTransaction()
                .add_token_transfer(token_id, self.operator_id, -amount)
                .add_token_transfer(token_id, receiver, amount)
                .execute(self.client) # auto-signs with operator’s key
        )
        if transfer_receipt.status != ResponseCode.SUCCESS:
            raise AssertionError(
                f"Transfer failed: {ResponseCode(transfer_receipt.status).name}"
            )

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
    
    assert token_receipt.status == ResponseCode.SUCCESS, f"Token creation failed with status: {ResponseCode(token_receipt.status).name}"
    
    return token_receipt.token_id

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
    
    assert token_receipt.status == ResponseCode.SUCCESS, f"Token creation failed with status: {ResponseCode(token_receipt.status).name}"
    
    return token_receipt.token_id