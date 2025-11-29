# Auto-generated proto imports per token module

token_proto_map = {
    'abstract_token_transfer_transaction': [
        ('hiero_sdk_python.hapi.services', 'basic_types_pb2'),
    ],
    'custom_fee': [
        ('hiero_sdk_python.hapi.services.basic_types_pb2', 'AccountID'),
        ('hiero_sdk_python.hapi.services.custom_fees_pb2', 'CustomFee'),
    ],
    'custom_fixed_fee': [
        ('hiero_sdk_python.hapi.services', 'custom_fees_pb2'),
        ('hiero_sdk_python.hapi.services', 'custom_fees_pb2'),
        ('hiero_sdk_python.hapi.services', 'custom_fees_pb2'),
        ('hiero_sdk_python.hapi.services', 'custom_fees_pb2'),
    ],
    'custom_fractional_fee': [
        ('hiero_sdk_python.hapi.services', 'custom_fees_pb2'),
        ('hiero_sdk_python.hapi.services', 'custom_fees_pb2'),
        ('hiero_sdk_python.hapi.services.basic_types_pb2', 'Fraction'),
    ],
    'custom_royalty_fee': [
        ('hiero_sdk_python.hapi.services', 'custom_fees_pb2'),
        ('hiero_sdk_python.hapi.services', 'custom_fees_pb2'),
        ('hiero_sdk_python.hapi.services.basic_types_pb2', 'Fraction'),
    ],
    'hbar_allowance': [
        ('hiero_sdk_python.hapi.services.crypto_approve_allowance_pb2', 'CryptoAllowance'),
    ],
    'hbar_transfer': [
        ('hiero_sdk_python.hapi.services', 'basic_types_pb2'),
    ],
    'nft_id': [
        ('hiero_sdk_python.hapi.services', 'basic_types_pb2'),
    ],
    'token_airdrop_claim': [
        ('hiero_sdk_python.hapi.services.token_claim_airdrop_pb2', 'TokenClaimAirdropTransactionBody'),
        ('hiero_sdk_python.hapi.services', 'transaction_pb2'),
    ],
    'token_airdrop_pending_id': [
        ('hiero_sdk_python.hapi.services', 'basic_types_pb2'),
    ],
    'token_airdrop_pending_record': [
        ('hiero_sdk_python.hapi.services', 'basic_types_pb2'),
        ('hiero_sdk_python.hapi.services', 'transaction_record_pb2'),
    ],
    'token_airdrop_transaction': [
        ('hiero_sdk_python.hapi.services', 'token_airdrop_pb2'),
        ('hiero_sdk_python.hapi.services', 'transaction_pb2'),
        ('hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2', 'SchedulableTransactionBody'),
    ],
    'token_airdrop_transaction_cancel': [
        ('hiero_sdk_python.hapi.services', 'basic_types_pb2'),
        ('hiero_sdk_python.hapi.services', 'token_cancel_airdrop_pb2'),
        ('hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2', 'SchedulableTransactionBody'),
    ],
    'token_allowance': [
        ('hiero_sdk_python.hapi.services.crypto_approve_allowance_pb2', 'TokenAllowance'),
    ],
    'token_associate_transaction': [
        ('hiero_sdk_python.hapi.services', 'token_associate_pb2'),
        ('hiero_sdk_python.hapi.services', 'transaction_pb2'),
        ('hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2', 'SchedulableTransactionBody'),
    ],
    'token_burn_transaction': [
        ('hiero_sdk_python.hapi.services.token_burn_pb2', 'TokenBurnTransactionBody'),
        ('hiero_sdk_python.hapi.services', 'transaction_pb2'),
        ('hiero_sdk_python.hapi.services', 'token_burn_pb2'),
        ('hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2', 'SchedulableTransactionBody'),
    ],
    'token_create_transaction': [
        ('hiero_sdk_python.hapi.services', 'token_create_pb2'),
        ('hiero_sdk_python.hapi.services', 'basic_types_pb2'),
        ('hiero_sdk_python.hapi.services', 'transaction_pb2'),
        ('hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2', 'SchedulableTransactionBody'),
    ],
    'token_delete_transaction': [
        ('hiero_sdk_python.hapi.services', 'token_delete_pb2'),
        ('hiero_sdk_python.hapi.services', 'transaction_pb2'),
        ('hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2', 'SchedulableTransactionBody'),
    ],
    'token_dissociate_transaction': [
        ('hiero_sdk_python.hapi.services', 'token_dissociate_pb2'),
        ('hiero_sdk_python.hapi.services', 'transaction_pb2'),
        ('hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2', 'SchedulableTransactionBody'),
    ],
    'token_fee_schedule_update_transaction': [
        ('hiero_sdk_python.hapi.services', 'token_fee_schedule_update_pb2'),
        ('hiero_sdk_python.hapi.services', 'transaction_pb2'),
        ('hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2', 'SchedulableTransactionBody'),
    ],
    'token_freeze_status': [
        ('hiero_sdk_python.hapi.services.basic_types_pb2', 'TokenFreezeStatus'),
    ],
    'token_freeze_transaction': [
        ('hiero_sdk_python.hapi.services', 'token_freeze_account_pb2'),
        ('hiero_sdk_python.hapi.services', 'transaction_pb2'),
        ('hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2', 'SchedulableTransactionBody'),
    ],
    'token_grant_kyc_transaction': [
        ('hiero_sdk_python.hapi.services.token_grant_kyc_pb2', 'TokenGrantKycTransactionBody'),
        ('hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2', 'SchedulableTransactionBody'),
        ('hiero_sdk_python.hapi.services', 'token_grant_kyc_pb2'),
        ('hiero_sdk_python.hapi.services', 'transaction_pb2'),
    ],
    'token_id': [
        ('hiero_sdk_python.hapi.services', 'basic_types_pb2'),
    ],
    'token_info': [
        ('hiero_sdk_python.hapi.services', 'token_get_info_pb2'),
    ],
    'token_key_validation': [
        ('hiero_sdk_python.hapi.services', 'basic_types_pb2'),
    ],
    'token_kyc_status': [
        ('hiero_sdk_python.hapi.services', 'basic_types_pb2'),
    ],
    'token_mint_transaction': [
        ('hiero_sdk_python.hapi.services.token_mint_pb2', 'TokenMintTransactionBody'),
        ('hiero_sdk_python.hapi.services', 'token_mint_pb2'),
        ('hiero_sdk_python.hapi.services', 'transaction_pb2'),
        ('hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2', 'SchedulableTransactionBody'),
    ],
    'token_nft_allowance': [
        ('hiero_sdk_python.hapi.services.crypto_approve_allowance_pb2', 'NftAllowance'),
        ('hiero_sdk_python.hapi.services.crypto_delete_allowance_pb2', 'NftRemoveAllowance'),
    ],
    'token_nft_info': [
        ('hiero_sdk_python.hapi.services', 'timestamp_pb2'),
        ('hiero_sdk_python.hapi.services', 'token_get_nft_info_pb2'),
    ],
    'token_nft_transfer': [
        ('hiero_sdk_python.hapi.services', 'basic_types_pb2'),
    ],
    'token_pause_status': [
        ('hiero_sdk_python.hapi.services', 'basic_types_pb2'),
    ],
    'token_pause_transaction': [
        ('hiero_sdk_python.hapi.services', 'transaction_pb2'),
        ('hiero_sdk_python.hapi.services', 'token_pause_pb2'),
        ('hiero_sdk_python.hapi.services.token_pause_pb2', 'TokenPauseTransactionBody'),
        ('hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2', 'SchedulableTransactionBody'),
    ],
    'token_reject_transaction': [
        ('hiero_sdk_python.hapi.services.token_reject_pb2', 'TokenReference'),
        ('hiero_sdk_python.hapi.services.token_reject_pb2', 'TokenRejectTransactionBody'),
        ('hiero_sdk_python.hapi.services', 'transaction_pb2'),
        ('hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2', 'SchedulableTransactionBody'),
    ],
    'token_relationship': [
        ('hiero_sdk_python.hapi.services.basic_types_pb2', 'TokenRelationship'),
        ('hiero_sdk_python.hapi.services.basic_types_pb2', 'TokenFreezeStatus'),
        ('hiero_sdk_python.hapi.services.basic_types_pb2', 'TokenKycStatus'),
    ],
    'token_revoke_kyc_transaction': [
        ('hiero_sdk_python.hapi.services.token_revoke_kyc_pb2', 'TokenRevokeKycTransactionBody'),
        ('hiero_sdk_python.hapi.services', 'token_revoke_kyc_pb2'),
        ('hiero_sdk_python.hapi.services', 'transaction_pb2'),
        ('hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2', 'SchedulableTransactionBody'),
    ],
    'token_transfer': [
        ('hiero_sdk_python.hapi.services', 'basic_types_pb2'),
    ],
    'token_transfer_list': [
        ('hiero_sdk_python.hapi.services', 'basic_types_pb2'),
    ],
    'token_unfreeze_transaction': [
        ('hiero_sdk_python.hapi.services', 'token_unfreeze_account_pb2'),
        ('hiero_sdk_python.hapi.services', 'transaction_pb2'),
        ('hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2', 'SchedulableTransactionBody'),
    ],
    'token_unpause_transaction': [
        ('hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2', 'SchedulableTransactionBody'),
        ('hiero_sdk_python.hapi.services.token_unpause_pb2', 'TokenUnpauseTransactionBody'),
        ('hiero_sdk_python.hapi.services.transaction_pb2', 'TransactionBody'),
    ],
    'token_update_nfts_transaction': [
        ('hiero_sdk_python.hapi.services.token_update_nfts_pb2', 'TokenUpdateNftsTransactionBody'),
        ('hiero_sdk_python.hapi.services', 'transaction_pb2'),
        ('hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2', 'SchedulableTransactionBody'),
        ('hiero_sdk_python.hapi.services', 'token_update_nfts_pb2'),
    ],
    'token_update_transaction': [
        ('hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2', 'SchedulableTransactionBody'),
        ('hiero_sdk_python.hapi.services', 'token_update_pb2'),
        ('hiero_sdk_python.hapi.services', 'transaction_pb2'),
    ],
    'token_wipe_transaction': [
        ('hiero_sdk_python.hapi.services', 'token_wipe_account_pb2'),
        ('hiero_sdk_python.hapi.services.token_wipe_account_pb2', 'TokenWipeAccountTransactionBody'),
        ('hiero_sdk_python.hapi.services', 'transaction_pb2'),
        ('hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2', 'SchedulableTransactionBody'),
    ],
}
