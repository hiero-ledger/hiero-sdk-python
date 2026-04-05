from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from tck.handlers.registry import rpc_method
from tck.param.account import CreateAccountParams
from tck.response.account import CreateAccountResponse
from tck.util.client_utils import get_client
from tck.util.constants import DEFAULT_GRPC_TIMEOUT
from tck.util.key_utils import get_key_from_string


def _build_create_account_transaction(params: CreateAccountParams) -> AccountCreateTransaction:
    transaction = AccountCreateTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.key is not None:
        transaction.set_key_without_alias(get_key_from_string(params.key))

    if params.initialBalance is not None:
        transaction.set_initial_balance(Hbar.from_tinybars(params.initialBalance))

    if params.receiverSignatureRequired is not None:
        transaction.set_receiver_signature_required(params.receiverSignatureRequired)

    if params.maxAutoTokenAssociations is not None:
        transaction.set_max_automatic_token_associations(params.maxAutoTokenAssociations)

    if params.stakedAccountId is not None:
        transaction.set_staked_account_id(AccountId.from_string(params.stakedAccountId))

    if params.stakedNodeId is not None:
        transaction.set_staked_node_id(params.stakedNodeId)

    if params.declineStakingReward is not None:
        transaction.set_decline_staking_reward(params.declineStakingReward)

    if params.memo is not None:
        transaction.set_account_memo(params.memo)

    if params.autoRenewPeriod is not None:
        transaction.set_auto_renew_period(params.autoRenewPeriod)

    if params.alias is not None:
        transaction.set_alias(params.alias)

    return transaction


@rpc_method("createAccount")
def create_account(params: CreateAccountParams) -> CreateAccountResponse:
    client = get_client(params.sessionId)

    transaction = _build_create_account_transaction(params)

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    response = transaction.execute(client, wait_for_receipt=False)
    receipt: TransactionReceipt = response.get_receipt(client, validate_status=True)

    account_id = ""
    if receipt.status == ResponseCode.SUCCESS:
        account_id = str(receipt.account_id)

    return CreateAccountResponse(account_id, ResponseCode(receipt.status).name)
