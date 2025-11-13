# Auto-generated transactions mapping

from hiero_sdk_python.tokens import (
    token_airdrop_transaction,
    token_associate_transaction,
    token_burn_transaction,
    token_create_transaction,
    token_delete_transaction,
    token_dissociate_transaction,
    token_fee_schedule_update_transaction,
    token_freeze_transaction,
    token_grant_kyc_transaction,
    token_mint_transaction,
    token_pause_transaction,
    token_reject_transaction,
    token_revoke_kyc_transaction,
    token_unfreeze_transaction,
    token_unpause_transaction,
    token_update_nfts_transaction,
    token_update_transaction,
    token_wipe_transaction,
)

from hiero_sdk_python.hapi.services import (
    schedulable_transaction_body_pb2,
    token_burn_pb2,
    token_grant_kyc_pb2,
    token_mint_pb2,
    token_pause_pb2,
    token_reject_pb2,
    token_revoke_kyc_pb2,
    token_update_nfts_pb2,
    token_wipe_account_pb2,
)

TRANSACTIONS = {
    'TokenFeeScheduleUpdateTransaction': {'cls': token_fee_schedule_update_transaction.TokenFeeScheduleUpdateTransaction, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
    'TokenFreezeTransaction': {'cls': token_freeze_transaction.TokenFreezeTransaction, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
    'TokenRevokeKycTransaction': {'cls': token_revoke_kyc_transaction.TokenRevokeKycTransaction, 'proto_cls': token_revoke_kyc_pb2.TokenRevokeKycTransactionBody},
    'AbstractTokenTransferTransaction': {'cls': token_airdrop_transaction.AbstractTokenTransferTransaction, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
    'TokenUpdateNftsTransaction': {'cls': token_update_nfts_transaction.TokenUpdateNftsTransaction, 'proto_cls': token_update_nfts_pb2.TokenUpdateNftsTransactionBody},
    'TokenAssociateTransaction': {'cls': token_associate_transaction.TokenAssociateTransaction, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
    'TokenMintTransaction': {'cls': token_mint_transaction.TokenMintTransaction, 'proto_cls': token_mint_pb2.TokenMintTransactionBody},
    'TokenCreateTransaction': {'cls': token_create_transaction.TokenCreateTransaction, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
    'TokenWipeTransaction': {'cls': token_wipe_transaction.TokenWipeTransaction, 'proto_cls': token_wipe_account_pb2.TokenWipeAccountTransactionBody},
    'TokenPauseTransaction': {'cls': token_pause_transaction.TokenPauseTransaction, 'proto_cls': token_pause_pb2.TokenPauseTransactionBody},
    'TokenBurnTransaction': {'cls': token_burn_transaction.TokenBurnTransaction, 'proto_cls': token_burn_pb2.TokenBurnTransactionBody},
    'TokenUnfreezeTransaction': {'cls': token_unfreeze_transaction.TokenUnfreezeTransaction, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
    'TokenRejectTransaction': {'cls': token_reject_transaction.TokenRejectTransaction, 'proto_cls': token_reject_pb2.TokenRejectTransactionBody},
    'TokenDissociateTransaction': {'cls': token_dissociate_transaction.TokenDissociateTransaction, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
    'TokenDeleteTransaction': {'cls': token_delete_transaction.TokenDeleteTransaction, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
    'TokenUnpauseTransaction': {'cls': token_unpause_transaction.TokenUnpauseTransaction, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
    'TokenUpdateTransaction': {'cls': token_update_transaction.TokenUpdateTransaction, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
    'TokenGrantKycTransaction': {'cls': token_grant_kyc_transaction.TokenGrantKycTransaction, 'proto_cls': token_grant_kyc_pb2.TokenGrantKycTransactionBody},
}

# Summary
TOTAL_TOKENS = 18
PROTO_IDENTIFIED = 18
UNMATCHED_TRANSACTIONS = []
