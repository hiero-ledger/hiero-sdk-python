# Auto-generated: mapping of src token classes to proto classes
# This file includes imports for IDE/Pylance support.

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

from hiero_sdk_python.hapi.services import basic_types_pb2
from hiero_sdk_python.hapi.services import crypto_approve_allowance_pb2
from hiero_sdk_python.hapi.services import crypto_delete_allowance_pb2
from hiero_sdk_python.hapi.services import custom_fees_pb2
from hiero_sdk_python.hapi.services import schedulable_transaction_body_pb2
from hiero_sdk_python.hapi.services import token_get_info_pb2
from hiero_sdk_python.hapi.services import token_get_nft_info_pb2
from hiero_sdk_python.hapi.services import token_update_nfts_pb2
from hiero_sdk_python.hapi.services import transaction_pb2
from hiero_sdk_python.hapi.services import transaction_record_pb2

TRANSACTIONS = {
    'AbstractTokenTransferTransaction': {'cls': abstract_token_transfer_transaction.AbstractTokenTransferTransaction, 'proto_cls': basic_types_pb2},
    'CustomFee': {'cls': custom_fee.CustomFee, 'proto_cls': None},
    'CustomFixedFee': {'cls': custom_fixed_fee.CustomFixedFee, 'proto_cls': custom_fees_pb2},
    'CustomFractionalFee': {'cls': custom_fractional_fee.CustomFractionalFee, 'proto_cls': None},
    'CustomRoyaltyFee': {'cls': custom_royalty_fee.CustomRoyaltyFee, 'proto_cls': None},
    'FeeAssessmentMethod': {'cls': fee_assessment_method.FeeAssessmentMethod, 'proto_cls': None},
    'HbarAllowance': {'cls': hbar_allowance.HbarAllowance, 'proto_cls': crypto_approve_allowance_pb2.CryptoAllowance},
    'HbarTransfer': {'cls': hbar_transfer.HbarTransfer, 'proto_cls': basic_types_pb2},
    'NftId': {'cls': nft_id.NftId, 'proto_cls': basic_types_pb2},
    'PendingAirdropId': {'cls': token_airdrop_pending_id.PendingAirdropId, 'proto_cls': basic_types_pb2},
    'PendingAirdropRecord': {'cls': token_airdrop_pending_record.PendingAirdropRecord, 'proto_cls': transaction_record_pb2},
    'SupplyType': {'cls': supply_type.SupplyType, 'proto_cls': None},
    'TokenAirdropTransaction': {'cls': token_airdrop_transaction.TokenAirdropTransaction, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
    'TokenAllowance': {'cls': token_allowance.TokenAllowance, 'proto_cls': crypto_approve_allowance_pb2.TokenAllowance},
    'TokenAssociateTransaction': {'cls': token_associate_transaction.TokenAssociateTransaction, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
    'TokenBurnTransaction': {'cls': token_burn_transaction.TokenBurnTransaction, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
    'TokenCancelAirdropTransaction': {'cls': token_airdrop_transaction_cancel.TokenCancelAirdropTransaction, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
    'TokenClaimAirdropTransaction': {'cls': token_airdrop_claim.TokenClaimAirdropTransaction, 'proto_cls': transaction_pb2},
    'TokenCreateTransaction': {'cls': token_create_transaction.TokenCreateTransaction, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
    'TokenCreateValidator': {'cls': token_create_transaction.TokenCreateValidator, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
    'TokenDeleteTransaction': {'cls': token_delete_transaction.TokenDeleteTransaction, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
    'TokenDissociateTransaction': {'cls': token_dissociate_transaction.TokenDissociateTransaction, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
    'TokenFeeScheduleUpdateTransaction': {'cls': token_fee_schedule_update_transaction.TokenFeeScheduleUpdateTransaction, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
    'TokenFreezeStatus': {'cls': token_freeze_status.TokenFreezeStatus, 'proto_cls': basic_types_pb2.TokenFreezeStatus},
    'TokenFreezeTransaction': {'cls': token_freeze_transaction.TokenFreezeTransaction, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
    'TokenGrantKycTransaction': {'cls': token_grant_kyc_transaction.TokenGrantKycTransaction, 'proto_cls': transaction_pb2},
    'TokenId': {'cls': token_id.TokenId, 'proto_cls': basic_types_pb2},
    'TokenInfo': {'cls': token_info.TokenInfo, 'proto_cls': token_get_info_pb2},
    'TokenKeyValidation': {'cls': token_key_validation.TokenKeyValidation, 'proto_cls': basic_types_pb2},
    'TokenKeys': {'cls': token_create_transaction.TokenKeys, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
    'TokenKycStatus': {'cls': token_kyc_status.TokenKycStatus, 'proto_cls': basic_types_pb2},
    'TokenMintTransaction': {'cls': token_mint_transaction.TokenMintTransaction, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
    'TokenNftAllowance': {'cls': token_nft_allowance.TokenNftAllowance, 'proto_cls': crypto_delete_allowance_pb2.NftRemoveAllowance},
    'TokenNftInfo': {'cls': token_nft_info.TokenNftInfo, 'proto_cls': token_get_nft_info_pb2},
    'TokenNftTransfer': {'cls': token_nft_transfer.TokenNftTransfer, 'proto_cls': basic_types_pb2},
    'TokenParams': {'cls': token_create_transaction.TokenParams, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
    'TokenPauseStatus': {'cls': token_pause_status.TokenPauseStatus, 'proto_cls': basic_types_pb2},
    'TokenPauseTransaction': {'cls': token_pause_transaction.TokenPauseTransaction, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
    'TokenRejectTransaction': {'cls': token_reject_transaction.TokenRejectTransaction, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
    'TokenRelationship': {'cls': token_relationship.TokenRelationship, 'proto_cls': basic_types_pb2.TokenKycStatus},
    'TokenRevokeKycTransaction': {'cls': token_revoke_kyc_transaction.TokenRevokeKycTransaction, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
    'TokenTransfer': {'cls': token_transfer.TokenTransfer, 'proto_cls': basic_types_pb2},
    'TokenTransferList': {'cls': token_transfer_list.TokenTransferList, 'proto_cls': basic_types_pb2},
    'TokenType': {'cls': token_type.TokenType, 'proto_cls': None},
    'TokenUnfreezeTransaction': {'cls': token_unfreeze_transaction.TokenUnfreezeTransaction, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
    'TokenUnpauseTransaction': {'cls': token_unpause_transaction.TokenUnpauseTransaction, 'proto_cls': transaction_pb2.TransactionBody},
    'TokenUpdateKeys': {'cls': token_update_transaction.TokenUpdateKeys, 'proto_cls': transaction_pb2},
    'TokenUpdateNftsTransaction': {'cls': token_update_nfts_transaction.TokenUpdateNftsTransaction, 'proto_cls': token_update_nfts_pb2},
    'TokenUpdateParams': {'cls': token_update_transaction.TokenUpdateParams, 'proto_cls': transaction_pb2},
    'TokenUpdateTransaction': {'cls': token_update_transaction.TokenUpdateTransaction, 'proto_cls': transaction_pb2},
    'TokenWipeTransaction': {'cls': token_wipe_transaction.TokenWipeTransaction, 'proto_cls': schedulable_transaction_body_pb2.SchedulableTransactionBody},
}
