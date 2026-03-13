
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.evm_address import EvmAddress
from hiero_sdk_python.exceptions import PrecheckError, ReceiptStatusError
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from tck.errors import JsonRpcError
from tck.handlers.registry import register_handler
from tck.handlers.sdk import CLIENTS
from tck.param.account import CreateAccountParams
from tck.response.account import CreateAccountResponse
from tck.util.key_utils import get_key_from_string


def _build_create_account_transaction(params: CreateAccountParams) -> AccountCreateTransaction:
  transaction = AccountCreateTransaction().set_grpc_deadline(30)
  
  if params.key:
    transaction.set_key_without_alias(get_key_from_string(params.key))
  
  if params.initialBalance:
    transaction.set_initial_balance(Hbar.from_tinybars(params.initialBalance))

  if params.receiverSignatureRequired:
    transaction.set_receiver_signature_required(params.receiverSignatureRequired)

  if params.maxAutoTokenAssociations is not None:
    transaction.set_max_automatic_token_associations(params.maxAutoTokenAssociations)
  
  if params.stakedAccountId:
    transaction.set_staked_account_id(AccountId.from_string(params.stakedAccountId))

  if params.stakedNodeId is not None:
    transaction.set_staked_node_id(params.stakedNodeId)

  if params.declineStakingReward:
    transaction.set_decline_staking_reward(params.declineStakingReward)
  
  if params.memo:
    transaction.set_account_memo(params.memo)
  
  if params.autoRenewPeriod:
    transaction.set_auto_renew_period(params.autoRenewPeriod)
  
  if params.alias:
    transaction.set_alias(EvmAddress.from_string(params.alias))

  return transaction


@register_handler("createAccount")
def create_account(params: CreateAccountParams) -> CreateAccountResponse:
  client = CLIENTS.get(params.sessionId)
  transaction = _build_create_account_transaction(params)
  
  if params.commonTransactionParams:
    params.commonTransactionParams.apply_common_params(transaction, client)
  
  response = transaction.execute(client, wait_for_receipt=False)
  print(response)
  receipt:TransactionReceipt = response.get_receipt(client)

  
  account_id = "";
  if receipt.status == ResponseCode.SUCCESS:
    account_id = str(receipt.account_id)

  return CreateAccountResponse(account_id, ResponseCode(receipt.status).name)  
