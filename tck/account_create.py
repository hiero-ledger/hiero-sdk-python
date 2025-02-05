import utils

from jsonrpcserver import method, Success
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from key_identifier import KeyIdentifier

@method
def createAccount(key: str = None, initialBalance: str = None, receiverSignatureRequired: bool = None, autoRenewPeriod: str = None,
    memo: str = None, maxAutoTokenAssociations: int = None, stakedAccountId: str = None, stakedNodeId: str = None,
    declineStakingReward: bool = None, alias: str = None, commonTransactionParams: dict = None):
    """
    :param key: string, optional, DER-encoded hex string representation for private or public keys. Keylists and threshold keys are the hex of the serialized protobuf bytes.
    :param initialBalance: Units of tinybars, optional
    :param receiverSignatureRequired: bool, optional
    :param autoRenewPeriod: string, Units of seconds, optional
    :param memo: string, optional
    :param maxAutoTokenAssociations: int32, optional
    :param stakedAccountId: string, optional
    :param stakedNodeId: string, optional
    :param declineStakingReward: bool, optional
    :param alias: string, optional, Hex string representation of the keccak-256 hash of an ECDSAsecp256k1 public key type.
    :param commonTransactionParams: JSON object, optional

    :return accountId: string, The ID of the created account.
    :return status:	string, The status of the submitted AccountCreateTransaction (from a TransactionReceipt).
    """
    key_and_public = KeyIdentifier.identify(key)

    if key_and_public[1] is False:
        public_key = key_and_public[0].public_key()
    else:
        public_key = key_and_public[0]

    # TODO: add all of the other transaction parameters
    transaction = (
        AccountCreateTransaction()
        .set_key(public_key)
        # .set_initial_balance(int(initialBalance))
        .set_receiver_signature_required(receiverSignatureRequired)
        # .set_auto_renew_period(0, int(autoRenewPeriod))
        .set_account_memo(memo)
        .freeze_with(utils.__client)
    )

    transaction.sign(utils.__operatorPrivateKey)
    receipt = transaction.execute(utils.__client)

    return Success({
        "accountId": str(receipt.accountId),
        "status": str(receipt.status),
    })
