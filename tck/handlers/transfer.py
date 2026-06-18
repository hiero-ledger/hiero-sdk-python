from __future__ import annotations

from hiero_sdk_python import (
    AccountId,
    NftId,
    TokenId,
    TransferTransaction,
)
from hiero_sdk_python.response_code import ResponseCode
from tck.handlers.registry import rpc_method
from tck.param.transfer import TransferCryptoParams
from tck.response.transfer import TransferCryptoResponse
from tck.util.client_utils import get_client
from tck.util.constants import DEFAULT_GRPC_TIMEOUT


def _build_transfer_transaction(params: TransferCryptoParams) -> TransferTransaction:
    tx = TransferTransaction()

    tx.set_grpc_deadline(DEFAULT_GRPC_TIMEOUT)

    if params.transfers is None:
        return tx

    for entry in params.transfers:
        ## HBAR Transfer
        if entry.hbar is not None:
            hbar = entry.hbar
            account = AccountId.from_string(hbar.evmAddress if hbar.evmAddress else hbar.accountId)
            amount = int(hbar.amount)

            if entry.approved:
                tx.add_approved_hbar_transfer(account, amount)
            else:
                tx.add_hbar_transfer(account, amount)

        ## Token Transfer
        elif entry.token is not None:
            token = entry.token

            token_id = TokenId.from_string(token.tokenId)
            account = AccountId.from_string(token.accountId)

            if token.decimals is not None:
                decimals = int(token.decimals)

                if entry.approved:
                    tx.add_approved_token_transfer_with_decimals(token_id, account, int(token.amount), decimals)
                else:
                    tx.add_token_transfer_with_decimals(token_id, account, int(token.amount), decimals)
            else:
                if entry.approved:
                    tx.add_approved_token_transfer(token_id, account, int(token.amount))
                else:
                    tx.add_token_transfer(token_id, account, int(token.amount))

        ## NFT Transfer
        elif entry.nft is not None:
            nft = entry.nft

            nft_id = NftId(TokenId.from_string(nft.tokenId), int(nft.serialNumber))

            sender = AccountId.from_string(nft.senderAccountId)
            receiver = AccountId.from_string(nft.receiverAccountId)

            if entry.approved:
                tx.add_approved_nft_transfer(nft_id, sender, receiver)
            else:
                tx.add_nft_transfer(nft_id, sender, receiver)

    return tx


@rpc_method("transferCrypto")
def transfer_crypto(params: TransferCryptoParams) -> TransferCryptoResponse:
    client = get_client(params.sessionId)

    tx = _build_transfer_transaction(params)

    if params.commonTransactionParams is not None:
        params.commonTransactionParams.apply_common_params(tx, client)

    receipt = tx.execute(client, wait_for_receipt=False).get_receipt(
        client,
        validate_status=True,
    )

    return TransferCryptoResponse(status=ResponseCode(receipt.status).name)
