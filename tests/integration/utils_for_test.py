import os
from pytest import fixture
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenType
from hiero_sdk_python.logger.log_level import LogLevel
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction, TokenKeys, TokenParams
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from hiero_sdk_python.hbar import Hbar

load_dotenv(override=True)


@fixture
def env():
    """Integration test environment with client/operator set up."""
    e = IntegrationTestEnv()
    yield e
    e.close()


@dataclass
class Account:
    id: AccountId
    key: PrivateKey


class IntegrationTestEnv:
    def __init__(self) -> None:
        network = Network(os.getenv("NETWORK", "testnet"))
        self.client = Client(network)

        self.operator_id: Optional[AccountId] = None
        self.operator_key: Optional[PrivateKey] = None

        operator_id = os.getenv("OPERATOR_ID")
        operator_key = os.getenv("OPERATOR_KEY")

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
            .freeze_with(self.client)
        )

        # ✅ Important: must sign with the operator’s key to authorize payment
        tx.sign(self.operator_key)

        receipt = tx.execute(self.client)
        if receipt.status != ResponseCode.SUCCESS:
            raise AssertionError(f"Account creation failed: {ResponseCode(receipt.status).name}")

        return Account(id=receipt.account_id, key=key)

    def associate_and_transfer(self, receiver: AccountId, receiver_key: PrivateKey, token_id, amount: int):
        """Associate token with receiver, then transfer `amount` from operator to receiver."""
        assoc_tx = (
            TokenAssociateTransaction()
            .set_account_id(receiver)
            .add_token_id(token_id)
            .freeze_with(self.client)
            .sign(receiver_key)
        )

        assoc_receipt = assoc_tx.execute(self.client)
        if assoc_receipt.status != ResponseCode.SUCCESS:
            raise AssertionError(f"Association failed: {ResponseCode(assoc_receipt.status).name}")

        transfer_tx = (
            TransferTransaction()
            .add_token_transfer(token_id, self.operator_id, -amount)
            .add_token_transfer(token_id, receiver, amount)
            .freeze_with(self.client)
        )

        # ✅ Again: ensure proper operator signing
        transfer_tx.sign(self.operator_key)
        transfer_receipt = transfer_tx.execute(self.client)

        if transfer_receipt.status != ResponseCode.SUCCESS:
            raise AssertionError(f"Transfer failed: {ResponseCode(transfer_receipt.status).name}")


# -------------------------------------------------------------------
# ✅ Token creation helpers
# -------------------------------------------------------------------

def create_fungible_token(env, opts=[], custom_fees=None):
    """Create a fungible token with given options and custom fees."""
    token_params = TokenParams(
        token_name="PTokenTest34",
        token_symbol="PTT34",
        decimals=2,
        initial_supply=1000,
        treasury_account_id=env.operator_id,
        token_type=TokenType.FUNGIBLE_COMMON,
        supply_type=SupplyType.FINITE,
        max_supply=10000,
    )

    token_keys = TokenKeys(
        admin_key=env.operator_key,
        supply_key=env.operator_key,
        freeze_key=env.operator_key,
        wipe_key=env.operator_key,
    )

    token_tx = TokenCreateTransaction(token_params, token_keys)

    # ✅ Fix: use set_custom_fees instead of deprecated add_custom_fee
    if custom_fees:
        token_tx.set_custom_fees(custom_fees)

    # Apply any optional modifiers
    for opt in opts:
        opt(token_tx)

    token_tx.freeze_with(env.client).sign(env.operator_key)
    token_receipt = token_tx.execute(env.client)

    assert token_receipt.status == ResponseCode.SUCCESS, (
        f"Token creation failed: {ResponseCode(token_receipt.status).name}"
    )

    return token_receipt.token_id


def create_nft_token(env, opts=[], custom_fees=None):
    """Create a non-fungible token (NFT) with given options and custom fees."""
    token_params = TokenParams(
        token_name="PythonNFTToken",
        token_symbol="PNFT",
        decimals=0,
        initial_supply=0,
        treasury_account_id=env.operator_id,
        token_type=TokenType.NON_FUNGIBLE_UNIQUE,
        supply_type=SupplyType.FINITE,
        max_supply=10000,
    )

    token_keys = TokenKeys(
        admin_key=env.operator_key,
        supply_key=env.operator_key,
        freeze_key=env.operator_key,
    )

    tx = TokenCreateTransaction(token_params, token_keys)

    # ✅ Updated API call
    if custom_fees:
        tx.set_custom_fees(custom_fees)

    for opt in opts:
        opt(tx)

    tx.freeze_with(env.client).sign(env.operator_key)
    token_receipt = tx.execute(env.client)

    assert token_receipt.status == ResponseCode.SUCCESS, (
        f"Token creation failed: {ResponseCode(token_receipt.status).name}"
    )

    return token_receipt.token_id
