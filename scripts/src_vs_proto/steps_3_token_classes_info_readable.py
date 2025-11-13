# Auto-generated class info: attributes, setters, other methods

from hiero_sdk_python.tokens import abstract_token_transfer_transaction
from hiero_sdk_python.tokens import custom_fee
from hiero_sdk_python.tokens import custom_fixed_fee
from hiero_sdk_python.tokens import custom_fractional_fee
from hiero_sdk_python.tokens import custom_royalty_fee
from hiero_sdk_python.tokens import fee_assessment_method
from hiero_sdk_python.tokens import hbar_allowance
from hiero_sdk_python.tokens import hbar_transfer
from hiero_sdk_python.tokens import nft_id
from hiero_sdk_python.tokens import supply_type
from hiero_sdk_python.tokens import token_airdrop_claim
from hiero_sdk_python.tokens import token_airdrop_pending_id
from hiero_sdk_python.tokens import token_airdrop_pending_record
from hiero_sdk_python.tokens import token_airdrop_transaction
from hiero_sdk_python.tokens import token_airdrop_transaction_cancel
from hiero_sdk_python.tokens import token_allowance
from hiero_sdk_python.tokens import token_associate_transaction
from hiero_sdk_python.tokens import token_burn_transaction
from hiero_sdk_python.tokens import token_create_transaction
from hiero_sdk_python.tokens import token_delete_transaction
from hiero_sdk_python.tokens import token_dissociate_transaction
from hiero_sdk_python.tokens import token_fee_schedule_update_transaction
from hiero_sdk_python.tokens import token_freeze_status
from hiero_sdk_python.tokens import token_freeze_transaction
from hiero_sdk_python.tokens import token_grant_kyc_transaction
from hiero_sdk_python.tokens import token_id
from hiero_sdk_python.tokens import token_info
from hiero_sdk_python.tokens import token_key_validation
from hiero_sdk_python.tokens import token_kyc_status
from hiero_sdk_python.tokens import token_mint_transaction
from hiero_sdk_python.tokens import token_nft_allowance
from hiero_sdk_python.tokens import token_nft_info
from hiero_sdk_python.tokens import token_nft_transfer
from hiero_sdk_python.tokens import token_pause_status
from hiero_sdk_python.tokens import token_pause_transaction
from hiero_sdk_python.tokens import token_reject_transaction
from hiero_sdk_python.tokens import token_relationship
from hiero_sdk_python.tokens import token_revoke_kyc_transaction
from hiero_sdk_python.tokens import token_transfer
from hiero_sdk_python.tokens import token_transfer_list
from hiero_sdk_python.tokens import token_type
from hiero_sdk_python.tokens import token_unfreeze_transaction
from hiero_sdk_python.tokens import token_unpause_transaction
from hiero_sdk_python.tokens import token_update_nfts_transaction
from hiero_sdk_python.tokens import token_update_transaction
from hiero_sdk_python.tokens import token_wipe_transaction

# File: abstract_token_transfer_transaction.py
abstract_token_transfer_transaction.AbstractTokenTransferTransaction = {
    'attributes': [
    ],
    'setters': [
        'add_token_transfer',
        'add_token_transfer_with_decimals',
        'add_approved_token_transfer',
        'add_approved_token_transfer_with_decimals',
        'add_nft_transfer',
        'add_approved_nft_transfer',
    ],
    'other_methods': [
        'build_token_transfers',
    ]
}

# File: custom_fee.py
custom_fee.CustomFee = {
    'attributes': [
        'fee_collector_account_id',
        'all_collectors_are_exempt',
    ],
    'setters': [
        'set_fee_collector_account_id',
        'set_all_collectors_are_exempt',
    ],
    'other_methods': [
    ]
}

# File: custom_fixed_fee.py
custom_fixed_fee.CustomFixedFee = {
    'attributes': [
        'amount',
        'denominating_token_id',
        'fee_collector_account_id',
        'all_collectors_are_exempt',
    ],
    'setters': [
        'set_amount_in_tinybars',
        'set_hbar_amount',
        'set_denominating_token_id',
        'set_denominating_token_to_same_token',
    ],
    'other_methods': [
    ]
}

# File: custom_fractional_fee.py
custom_fractional_fee.CustomFractionalFee = {
    'attributes': [
        'numerator',
        'denominator',
        'min_amount',
        'max_amount',
        'assessment_method',
        'fee_collector_account_id',
        'all_collectors_are_exempt',
    ],
    'setters': [
        'set_numerator',
        'set_denominator',
        'set_min_amount',
        'set_max_amount',
        'set_assessment_method',
    ],
    'other_methods': [
    ]
}

# File: custom_royalty_fee.py
custom_royalty_fee.CustomRoyaltyFee = {
    'attributes': [
        'numerator',
        'denominator',
        'fallback_fee',
        'fee_collector_account_id',
        'all_collectors_are_exempt',
    ],
    'setters': [
        'set_numerator',
        'set_denominator',
        'set_fallback_fee',
    ],
    'other_methods': [
    ]
}

# File: fee_assessment_method.py
fee_assessment_method.FeeAssessmentMethod = {
    'attributes': [
    ],
    'setters': [
    ],
    'other_methods': [
    ]
}

# File: hbar_allowance.py
hbar_allowance.HbarAllowance = {
    'attributes': [
    ],
    'setters': [
    ],
    'other_methods': [
    ]
}

# File: hbar_transfer.py
hbar_transfer.HbarTransfer = {
    'attributes': [
        'account_id',
        'amount',
        'is_approved',
    ],
    'setters': [
    ],
    'other_methods': [
    ]
}

# File: nft_id.py
nft_id.NftId = {
    'attributes': [
        'token_id',
        'serial_number',
    ],
    'setters': [
    ],
    'other_methods': [
        'from_string',
        'to_string_with_checksum',
    ]
}

# File: supply_type.py
supply_type.SupplyType = {
    'attributes': [
    ],
    'setters': [
    ],
    'other_methods': [
    ]
}

# File: token_airdrop_claim.py
token_airdrop_claim.TokenClaimAirdropTransaction = {
    'attributes': [
        'pending_airdrop_ids',
    ],
    'setters': [
        'add_pending_airdrop_id',
        'add_pending_airdrop_ids',
    ],
    'other_methods': [
        'build_transaction_body',
        'get_pending_airdrop_ids',
    ]
}

# File: token_airdrop_pending_id.py
token_airdrop_pending_id.PendingAirdropId = {
    'attributes': [
        'sender_id',
        'receiver_id',
        'token_id',
        'nft_id',
    ],
    'setters': [
    ],
    'other_methods': [
    ]
}

# File: token_airdrop_pending_record.py
token_airdrop_pending_record.PendingAirdropRecord = {
    'attributes': [
        'pending_airdrop_id',
        'amount',
    ],
    'setters': [
    ],
    'other_methods': [
    ]
}

# File: token_airdrop_transaction.py
token_airdrop_transaction.TokenAirdropTransaction = {
    'attributes': [
        'token_transfers',
        'nft_transfers',
    ],
    'setters': [
    ],
    'other_methods': [
        'build_transaction_body',
        'build_scheduled_body',
    ]
}

# File: token_airdrop_transaction_cancel.py
token_airdrop_transaction_cancel.TokenCancelAirdropTransaction = {
    'attributes': [
        'pending_airdrops',
    ],
    'setters': [
        'set_pending_airdrops',
        'add_pending_airdrop',
    ],
    'other_methods': [
        'clear_pending_airdrops',
        'build_transaction_body',
        'build_scheduled_body',
    ]
}

# File: token_allowance.py
token_allowance.TokenAllowance = {
    'attributes': [
    ],
    'setters': [
    ],
    'other_methods': [
    ]
}

# File: token_associate_transaction.py
token_associate_transaction.TokenAssociateTransaction = {
    'attributes': [
        'account_id',
        'token_ids',
    ],
    'setters': [
        'set_account_id',
        'add_token_id',
    ],
    'other_methods': [
        'build_transaction_body',
        'build_scheduled_body',
    ]
}

# File: token_burn_transaction.py
token_burn_transaction.TokenBurnTransaction = {
    'attributes': [
        'token_id',
        'amount',
        'serials',
    ],
    'setters': [
        'set_token_id',
        'set_amount',
        'set_serials',
        'add_serial',
    ],
    'other_methods': [
        'build_transaction_body',
        'build_scheduled_body',
    ]
}

# File: token_create_transaction.py
token_create_transaction.TokenCreateTransaction = {
    'attributes': [
        'token_params',
        'keys',
    ],
    'setters': [
        'set_token_params',
        'set_token_keys',
        'set_token_name',
        'set_token_symbol',
        'set_treasury_account_id',
        'set_decimals',
        'set_initial_supply',
        'set_token_type',
        'set_max_supply',
        'set_supply_type',
        'set_freeze_default',
        'set_expiration_time',
        'set_auto_renew_period',
        'set_auto_renew_account_id',
        'set_memo',
        'set_admin_key',
        'set_supply_key',
        'set_freeze_key',
        'set_wipe_key',
        'set_metadata_key',
        'set_pause_key',
        'set_kyc_key',
        'set_custom_fees',
        'set_fee_schedule_key',
    ],
    'other_methods': [
        'freeze_with',
        'build_transaction_body',
        'build_scheduled_body',
    ]
}

# File: token_create_transaction.py
token_create_transaction.TokenCreateValidator = {
    'attributes': [
    ],
    'setters': [
    ],
    'other_methods': [
    ]
}

# File: token_create_transaction.py
token_create_transaction.TokenKeys = {
    'attributes': [
    ],
    'setters': [
    ],
    'other_methods': [
    ]
}

# File: token_create_transaction.py
token_create_transaction.TokenParams = {
    'attributes': [
    ],
    'setters': [
    ],
    'other_methods': [
    ]
}

# File: token_delete_transaction.py
token_delete_transaction.TokenDeleteTransaction = {
    'attributes': [
        'token_id',
    ],
    'setters': [
        'set_token_id',
    ],
    'other_methods': [
        'build_transaction_body',
        'build_scheduled_body',
    ]
}

# File: token_dissociate_transaction.py
token_dissociate_transaction.TokenDissociateTransaction = {
    'attributes': [
        'account_id',
        'token_ids',
    ],
    'setters': [
        'set_account_id',
        'add_token_id',
    ],
    'other_methods': [
        'build_transaction_body',
        'build_scheduled_body',
    ]
}

# File: token_fee_schedule_update_transaction.py
token_fee_schedule_update_transaction.TokenFeeScheduleUpdateTransaction = {
    'attributes': [
        'token_id',
        'custom_fees',
    ],
    'setters': [
        'set_token_id',
        'set_custom_fees',
    ],
    'other_methods': [
        'build_transaction_body',
        'build_scheduled_body',
    ]
}

# File: token_freeze_status.py
token_freeze_status.TokenFreezeStatus = {
    'attributes': [
    ],
    'setters': [
    ],
    'other_methods': [
    ]
}

# File: token_freeze_transaction.py
token_freeze_transaction.TokenFreezeTransaction = {
    'attributes': [
        'token_id',
        'account_id',
    ],
    'setters': [
        'set_token_id',
        'set_account_id',
    ],
    'other_methods': [
        'build_transaction_body',
        'build_scheduled_body',
    ]
}

# File: token_grant_kyc_transaction.py
token_grant_kyc_transaction.TokenGrantKycTransaction = {
    'attributes': [
        'token_id',
        'account_id',
    ],
    'setters': [
        'set_token_id',
        'set_account_id',
    ],
    'other_methods': [
        'build_transaction_body',
        'build_scheduled_body',
    ]
}

# File: token_id.py
token_id.TokenId = {
    'attributes': [
    ],
    'setters': [
    ],
    'other_methods': [
        'from_string',
        'validate_checksum',
        'to_string_with_checksum',
    ]
}

# File: token_info.py
token_info.TokenInfo = {
    'attributes': [
    ],
    'setters': [
        'set_admin_key',
        'set_kyc_key',
        'set_freeze_key',
        'set_wipe_key',
        'set_supply_key',
        'set_metadata_key',
        'set_fee_schedule_key',
        'set_default_freeze_status',
        'set_default_kyc_status',
        'set_auto_renew_account',
        'set_auto_renew_period',
        'set_expiry',
        'set_pause_key',
        'set_pause_status',
        'set_supply_type',
        'set_metadata',
        'set_custom_fees',
    ],
    'other_methods': [
    ]
}

# File: token_key_validation.py
token_key_validation.TokenKeyValidation = {
    'attributes': [
    ],
    'setters': [
    ],
    'other_methods': [
    ]
}

# File: token_kyc_status.py
token_kyc_status.TokenKycStatus = {
    'attributes': [
    ],
    'setters': [
    ],
    'other_methods': [
    ]
}

# File: token_mint_transaction.py
token_mint_transaction.TokenMintTransaction = {
    'attributes': [
        'token_id',
        'amount',
        'metadata',
    ],
    'setters': [
        'set_token_id',
        'set_amount',
        'set_metadata',
    ],
    'other_methods': [
        'build_transaction_body',
        'build_scheduled_body',
    ]
}

# File: token_nft_allowance.py
token_nft_allowance.TokenNftAllowance = {
    'attributes': [
    ],
    'setters': [
    ],
    'other_methods': [
    ]
}

# File: token_nft_info.py
token_nft_info.TokenNftInfo = {
    'attributes': [
    ],
    'setters': [
    ],
    'other_methods': [
    ]
}

# File: token_nft_transfer.py
token_nft_transfer.TokenNftTransfer = {
    'attributes': [
        'token_id',
        'sender_id',
        'receiver_id',
        'serial_number',
        'is_approved',
    ],
    'setters': [
    ],
    'other_methods': [
    ]
}

# File: token_pause_status.py
token_pause_status.TokenPauseStatus = {
    'attributes': [
    ],
    'setters': [
    ],
    'other_methods': [
    ]
}

# File: token_pause_transaction.py
token_pause_transaction.TokenPauseTransaction = {
    'attributes': [
        'token_id',
    ],
    'setters': [
        'set_token_id',
    ],
    'other_methods': [
        'build_transaction_body',
        'build_scheduled_body',
    ]
}

# File: token_reject_transaction.py
token_reject_transaction.TokenRejectTransaction = {
    'attributes': [
        'owner_id',
        'token_ids',
        'nft_ids',
    ],
    'setters': [
        'set_owner_id',
        'set_token_ids',
        'set_nft_ids',
    ],
    'other_methods': [
        'build_transaction_body',
        'build_scheduled_body',
    ]
}

# File: token_relationship.py
token_relationship.TokenRelationship = {
    'attributes': [
    ],
    'setters': [
    ],
    'other_methods': [
    ]
}

# File: token_revoke_kyc_transaction.py
token_revoke_kyc_transaction.TokenRevokeKycTransaction = {
    'attributes': [
        'token_id',
        'account_id',
    ],
    'setters': [
        'set_token_id',
        'set_account_id',
    ],
    'other_methods': [
        'build_transaction_body',
        'build_scheduled_body',
    ]
}

# File: token_transfer.py
token_transfer.TokenTransfer = {
    'attributes': [
        'token_id',
        'account_id',
        'amount',
        'expected_decimals',
        'is_approved',
    ],
    'setters': [
    ],
    'other_methods': [
    ]
}

# File: token_transfer_list.py
token_transfer_list.TokenTransferList = {
    'attributes': [
        'token',
        'transfers',
        'nft_transfers',
        'expected_decimals',
    ],
    'setters': [
        'add_token_transfer',
        'add_nft_transfer',
    ],
    'other_methods': [
    ]
}

# File: token_type.py
token_type.TokenType = {
    'attributes': [
    ],
    'setters': [
    ],
    'other_methods': [
    ]
}

# File: token_unfreeze_transaction.py
token_unfreeze_transaction.TokenUnfreezeTransaction = {
    'attributes': [
        'account_id',
        'token_id',
    ],
    'setters': [
        'set_token_id',
        'set_account_id',
    ],
    'other_methods': [
        'build_transaction_body',
        'build_scheduled_body',
    ]
}

# File: token_unpause_transaction.py
token_unpause_transaction.TokenUnpauseTransaction = {
    'attributes': [
        'token_id',
    ],
    'setters': [
        'set_token_id',
    ],
    'other_methods': [
        'build_transaction_body',
        'build_scheduled_body',
    ]
}

# File: token_update_nfts_transaction.py
token_update_nfts_transaction.TokenUpdateNftsTransaction = {
    'attributes': [
        'token_id',
        'serial_numbers',
        'metadata',
    ],
    'setters': [
        'set_token_id',
        'set_serial_numbers',
        'set_metadata',
    ],
    'other_methods': [
        'build_transaction_body',
        'build_scheduled_body',
    ]
}

# File: token_update_transaction.py
token_update_transaction.TokenUpdateKeys = {
    'attributes': [
    ],
    'setters': [
    ],
    'other_methods': [
    ]
}

# File: token_update_transaction.py
token_update_transaction.TokenUpdateParams = {
    'attributes': [
    ],
    'setters': [
    ],
    'other_methods': [
    ]
}

# File: token_update_transaction.py
token_update_transaction.TokenUpdateTransaction = {
    'attributes': [
        'token_id',
        'token_params',
        'token_keys',
        'token_key_verification_mode',
    ],
    'setters': [
        'set_token_id',
        'set_treasury_account_id',
        'set_token_name',
        'set_token_symbol',
        'set_token_memo',
        'set_metadata',
        'set_auto_renew_account_id',
        'set_auto_renew_period',
        'set_expiration_time',
        'set_admin_key',
        'set_freeze_key',
        'set_wipe_key',
        'set_supply_key',
        'set_pause_key',
        'set_metadata_key',
        'set_kyc_key',
        'set_fee_schedule_key',
        'set_key_verification_mode',
    ],
    'other_methods': [
        'build_transaction_body',
        'build_scheduled_body',
    ]
}

# File: token_wipe_transaction.py
token_wipe_transaction.TokenWipeTransaction = {
    'attributes': [
        'token_id',
        'account_id',
        'amount',
        'serial',
    ],
    'setters': [
        'set_token_id',
        'set_account_id',
        'set_amount',
        'set_serial',
    ],
    'other_methods': [
        'build_transaction_body',
        'build_scheduled_body',
    ]
}

