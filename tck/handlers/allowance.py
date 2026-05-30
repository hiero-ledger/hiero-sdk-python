"""TCK RPC handler for the approveAllowance endpoint."""

from __future__ import annotations

from hiero_sdk_python.account.account_allowance_approve_transaction import (
    AccountAllowanceApproveTransaction,
)
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from tck.handlers.registry import rpc_method
from tck.param.allowance import AllowanceEntry, ApproveAllowanceParams
from tck.response.allowance import ApproveAllowanceResponse
from tck.util.client_utils import get_client
from tck.util.constants import DEFAULT_GRPC_TIMEOUT


def _build_approve_allowance_transaction(
    params: ApproveAllowanceParams,
) -> AccountAllowanceApproveTransaction:
    """Build an AccountAllowanceApproveTransaction from TCK params."""
    transaction = AccountAllowanceApproveTransaction().set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if not params.allowances:
        raise ValueError("allowances list cannot be empty")

    for entry in params.allowances:
        _apply_allowance_entry(transaction, entry)

    return transaction


def _parse_optional_account_id(value: str | None) -> AccountId | None:
    """Parse an optional account ID string, raising on empty string."""
    if value is None:
        return None
    if not value.strip():
        raise ValueError("Account ID cannot be an empty string")
    return AccountId.from_string(value)


def _apply_allowance_entry(
    transaction: AccountAllowanceApproveTransaction,
    entry: AllowanceEntry,
) -> None:
    """Apply a single allowance entry to the transaction."""
    owner_account_id = _parse_optional_account_id(entry.ownerAccountId)
    spender_account_id = _parse_optional_account_id(entry.spenderAccountId)

    if entry.hbar is not None:
        amount = int(entry.hbar.amount)
        transaction.approve_hbar_allowance(
            owner_account_id,
            spender_account_id,
            Hbar.from_tinybars(amount),
        )

    if entry.token is not None:
        token_id = TokenId.from_string(entry.token.tokenId)
        amount = int(entry.token.amount)
        transaction.approve_token_allowance(
            token_id,
            owner_account_id,
            spender_account_id,
            amount,
        )

    if entry.nft is not None:
        token_id = TokenId.from_string(entry.nft.tokenId)

        if entry.nft.approvedForAll is True:
            transaction.approve_token_nft_allowance_all_serials(
                token_id,
                owner_account_id,
                spender_account_id,
            )
        elif entry.nft.approvedForAll is False:
            transaction.delete_token_nft_allowance_all_serials(
                token_id,
                owner_account_id,
                spender_account_id,
            )
        elif entry.nft.serialNumbers is not None:
            delegating_spender = None
            if entry.nft.delegateSpenderAccountId:
                delegating_spender = AccountId.from_string(entry.nft.delegateSpenderAccountId)

            for serial in entry.nft.serialNumbers:
                nft_id = NftId(token_id=token_id, serial_number=int(serial))
                if delegating_spender is not None:
                    transaction.approve_token_nft_allowance_with_delegating_spender(
                        nft_id,
                        owner_account_id,
                        spender_account_id,
                        delegating_spender,
                    )
                else:
                    transaction.approve_token_nft_allowance(
                        nft_id,
                        owner_account_id,
                        spender_account_id,
                    )
        else:
            # nft object present with only tokenId — this is DeleteNftAllowanceAllSerials
            # with no approvedForAll field (defaults to delete)
            transaction.delete_token_nft_allowance_all_serials(
                token_id,
                owner_account_id,
                spender_account_id,
            )


@rpc_method("approveAllowance")
def approve_allowance(params: ApproveAllowanceParams) -> ApproveAllowanceResponse:
    """Approve allowances using TCK approveAllowance parameters."""
    client = get_client(params.sessionId)

    transaction = _build_approve_allowance_transaction(params)

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(transaction, client)

    response = transaction.execute(client, wait_for_receipt=False)
    receipt: TransactionReceipt = response.get_receipt(client, validate_status=True)

    return ApproveAllowanceResponse(status=ResponseCode(receipt.status).name)
