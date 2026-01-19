"""
Integration tests for AccountId.
"""

import time
import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.transaction_get_receipt_query import TransactionGetReceiptQuery
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from tests.integration.utils import env

@pytest.fixture
def evm_address():
    """Returns an evm_address."""
    private_key = PrivateKey.generate_ecdsa()
    public_key = private_key.public_key()

    return public_key.to_evm_address()

@pytest.mark.integration
def test_populate_account_id_num(env, evm_address):
    """Test populate AccountId num from mirror node."""
    evm_address_account = AccountId.from_evm_address(evm_address, 0, 0)

    # Auto account creation by doing transfer to an evm_address
    transfer_tx = (
        TransferTransaction()
        .add_hbar_transfer(evm_address_account, Hbar(1).to_tinybars())
        .add_hbar_transfer(env.operator_id, Hbar(-1).to_tinybars())
    )
    transfer_tx.execute(env.client)

    transfer_receipt = (
        TransactionGetReceiptQuery()
        .set_transaction_id(transfer_tx.transaction_id)
        .set_include_children(True)
        .execute(env.client)
    )

    assert transfer_receipt is not None
    assert len(transfer_receipt.children) > 0

    account_id = transfer_receipt.children[0].account_id
    
    assert account_id is not None

    # Wait for mirrornode to update
    time.sleep(5)

    mirror_account_id = AccountId.from_evm_address(evm_address, 0, 0)

    assert mirror_account_id.num == 0

    mirror_account_id.populate_account_num(env.client)
    
    assert mirror_account_id.shard == account_id.shard
    assert mirror_account_id.realm == account_id.realm
    assert mirror_account_id.num == account_id.num


@pytest.mark.integration
def test_populate_account_id_evm_address(env, evm_address):
    """Test populate AccountId evm address from mirror node."""
    evm_address_account = AccountId.from_evm_address(evm_address, 0, 0)

    # Auto account creation by doing transfer to an evm_address
    transfer_tx = (
        TransferTransaction()
        .add_hbar_transfer(evm_address_account, Hbar(1).to_tinybars())
        .add_hbar_transfer(env.operator_id, Hbar(-1).to_tinybars())
    )
    transfer_tx.execute(env.client)

    transfer_receipt = (
        TransactionGetReceiptQuery()
        .set_transaction_id(transfer_tx.transaction_id)
        .set_include_children(True)
        .execute(env.client)
    )

    assert transfer_receipt is not None
    assert len(transfer_receipt.children) > 0

    account_id = transfer_receipt.children[0].account_id

    # Wait for mirrornode to update
    time.sleep(5)

    assert account_id.evm_address is None
    account_id.populate_evm_address(env.client)

    assert account_id.evm_address is not None
    assert account_id.evm_address == evm_address
