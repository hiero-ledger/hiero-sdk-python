# Auto-generated class info: imports, attributes and setters

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
    ]
}

# File: fee_assessment_method.py
fee_assessment_method.FeeAssessmentMethod = {
    'attributes': [
    ],
    'setters': [
    ]
}

# File: hbar_allowance.py
hbar_allowance.HbarAllowance = {
    'attributes': [
    ],
    'setters': [
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
    ]
}

# File: nft_id.py
nft_id.NftId = {
    'attributes': [
        'token_id',
        'serial_number',
    ],
    'setters': [
    ]
}

# File: supply_type.py
supply_type.SupplyType = {
    'attributes': [
    ],
    'setters': [
    ]
}

# File: token_airdrop_claim.py
token_airdrop_claim.TokenClaimAirdropTransaction = {
    'attributes': [
        'pending_airdrop_ids',
    ],
    'setters': [
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
    ]
}

# File: token_airdrop_pending_record.py
token_airdrop_pending_record.PendingAirdropRecord = {
    'attributes': [
        'pending_airdrop_id',
        'amount',
    ],
    'setters': [
    ]
}

# File: token_airdrop_transaction.py
token_airdrop_transaction.TokenAirdropTransaction = {
    'attributes': [
        'token_transfers',
        'nft_transfers',
    ],
    'setters': [
    ]
}

# File: token_airdrop_transaction_cancel.py
token_airdrop_transaction_cancel.TokenCancelAirdropTransaction = {
    'attributes': [
        'pending_airdrops',
    ],
    'setters': [
        'set_pending_airdrops',
    ]
}

# File: token_allowance.py
token_allowance.TokenAllowance = {
    'attributes': [
    ],
    'setters': [
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
    ]
}

# File: token_create_transaction.py
token_create_transaction.TokenCreateValidator = {
    'attributes': [
    ],
    'setters': [
    ]
}

# File: token_create_transaction.py
token_create_transaction.TokenKeys = {
    'attributes': [
    ],
    'setters': [
    ]
}

# File: token_create_transaction.py
token_create_transaction.TokenParams = {
    'attributes': [
    ],
    'setters': [
    ]
}

# File: token_delete_transaction.py
token_delete_transaction.TokenDeleteTransaction = {
    'attributes': [
        'token_id',
    ],
    'setters': [
        'set_token_id',
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
    ]
}

# File: token_freeze_status.py
token_freeze_status.TokenFreezeStatus = {
    'attributes': [
    ],
    'setters': [
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
    ]
}

# File: token_id.py
token_id.TokenId = {
    'attributes': [
    ],
    'setters': [
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
    ]
}

# File: token_key_validation.py
token_key_validation.TokenKeyValidation = {
    'attributes': [
    ],
    'setters': [
    ]
}

# File: token_kyc_status.py
token_kyc_status.TokenKycStatus = {
    'attributes': [
    ],
    'setters': [
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
    ]
}

# File: token_nft_allowance.py
token_nft_allowance.TokenNftAllowance = {
    'attributes': [
    ],
    'setters': [
    ]
}

# File: token_nft_info.py
token_nft_info.TokenNftInfo = {
    'attributes': [
    ],
    'setters': [
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
    ]
}

# File: token_pause_status.py
token_pause_status.TokenPauseStatus = {
    'attributes': [
    ],
    'setters': [
    ]
}

# File: token_pause_transaction.py
token_pause_transaction.TokenPauseTransaction = {
    'attributes': [
        'token_id',
    ],
    'setters': [
        'set_token_id',
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
    ]
}

# File: token_relationship.py
token_relationship.TokenRelationship = {
    'attributes': [
    ],
    'setters': [
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
    ]
}

# File: token_type.py
token_type.TokenType = {
    'attributes': [
    ],
    'setters': [
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
    ]
}

# File: token_unpause_transaction.py
token_unpause_transaction.TokenUnpauseTransaction = {
    'attributes': [
        'token_id',
    ],
    'setters': [
        'set_token_id',
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
    ]
}

# File: token_update_transaction.py
token_update_transaction.TokenUpdateKeys = {
    'attributes': [
    ],
    'setters': [
    ]
}

# File: token_update_transaction.py
token_update_transaction.TokenUpdateParams = {
    'attributes': [
    ],
    'setters': [
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
    ]
}

