from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from hiero_sdk_python.transaction.transaction_id import TransactionId

def build_query_payment_transaction(
    payer_account_id: AccountId,
    payer_private_key: PrivateKey,
    node_account_id: AccountId,
    amount: Hbar
) -> TransferTransaction:
    """
    Build and sign a TransferTransaction that sends `amount` of HBAR from
    `payer_account_id` to `node_account_id`. Returns a Transaction proto
    that can be attached to QueryHeader.payment.
    """

    tx = TransferTransaction()
    tx.add_hbar_transfer(payer_account_id, -amount.to_tinybars())
    tx.add_hbar_transfer(node_account_id, amount.to_tinybars())

    tx.transaction_fee = 100_000_000 
    tx.node_account_id = node_account_id
    tx.transaction_id = TransactionId.generate(payer_account_id)

    body_bytes = tx.build_transaction_body().SerializeToString()
    tx._transaction_body_bytes.setdefault(node_account_id, body_bytes)

    tx.sign(payer_private_key)
    return tx._to_proto()
