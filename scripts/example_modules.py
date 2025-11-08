# Auto-generated module imports for run_examples.py

import examples.account_allowance_hbar as account_allowance_hbar
import examples.account_allowance_nft as account_allowance_nft
import examples.account_create as account_create
import examples.account_delete as account_delete
import examples.account_id as account_id
import examples.account_update as account_update
import examples.contract_create as contract_create
import examples.contract_create_constructor as contract_create_constructor
import examples.contract_create_with_bytecode as contract_create_with_bytecode
import examples.contract_delete as contract_delete
import examples.contract_execute as contract_execute
import examples.contract_execute_with_value as contract_execute_with_value
import examples.contract_update as contract_update
import examples.custom_fee_fixed as custom_fee_fixed
import examples.custom_fee_fractional as custom_fee_fractional
import examples.custom_fee_royalty as custom_fee_royalty
import examples.ethereum_transaction_execute as ethereum_transaction_execute
import examples.file_append as file_append
import examples.file_create as file_create
import examples.file_delete as file_delete
import examples.file_update as file_update
import examples.keys_private_der as keys_private_der
import examples.keys_private_ecdsa as keys_private_ecdsa
import examples.keys_private_ed25519 as keys_private_ed25519
import examples.keys_public_der as keys_public_der
import examples.keys_public_ecdsa as keys_public_ecdsa
import examples.keys_public_ed25519 as keys_public_ed25519
import examples.logging_example as logging_example
import examples.prng_transaction as prng_transaction
import examples.query_account_info as query_account_info
import examples.query_account_records as query_account_records
import examples.query_balance as query_balance
import examples.query_contract_bytecode as query_contract_bytecode
import examples.query_contract_call as query_contract_call
import examples.query_contract_info as query_contract_info
import examples.query_file_contents as query_file_contents
import examples.query_file_info as query_file_info
import examples.query_nft_info as query_nft_info
import examples.query_payment as query_payment
import examples.query_receipt as query_receipt
import examples.query_record as query_record
import examples.query_schedule_info as query_schedule_info
import examples.query_token_info_fungible as query_token_info_fungible
import examples.query_token_info_nft as query_token_info_nft
import examples.query_topic_info as query_topic_info
import examples.query_topic_message as query_topic_message
import examples.revenue_generating_topics as revenue_generating_topics
import examples.schedule_account_create as schedule_account_create
import examples.schedule_delete as schedule_delete
import examples.schedule_sign as schedule_sign
import examples.token_airdrop as token_airdrop
import examples.token_airdrop_cancel as token_airdrop_cancel
import examples.token_airdrop_claim_signature_not_required_auto as token_airdrop_claim_signature_not_required_auto
import examples.token_airdrop_claim_signature_required as token_airdrop_claim_signature_required
import examples.token_allowance as token_allowance
import examples.token_associate as token_associate
import examples.token_burn_fungible as token_burn_fungible
import examples.token_burn_nft as token_burn_nft
import examples.token_create_fungible_finite as token_create_fungible_finite
import examples.token_create_fungible_infinite as token_create_fungible_infinite
import examples.token_create_nft_finite as token_create_nft_finite
import examples.token_create_nft_infinite as token_create_nft_infinite
import examples.token_delete as token_delete
import examples.token_dissociate as token_dissociate
import examples.token_freeze as token_freeze
import examples.token_grant_kyc as token_grant_kyc
import examples.token_mint_fungible as token_mint_fungible
import examples.token_mint_non_fungible as token_mint_non_fungible
import examples.token_pause as token_pause
import examples.token_reject_fungible_token as token_reject_fungible_token
import examples.token_reject_nft as token_reject_nft
import examples.token_revoke_kyc as token_revoke_kyc
import examples.token_unfreeze as token_unfreeze
import examples.token_unpause as token_unpause
import examples.token_update_fee_schedule_fungible as token_update_fee_schedule_fungible
import examples.token_update_fee_schedule_nft as token_update_fee_schedule_nft
import examples.token_update_fungible as token_update_fungible
import examples.token_update_key as token_update_key
import examples.token_update_nft as token_update_nft
import examples.token_update_nfts as token_update_nfts
import examples.token_wipe as token_wipe
import examples.topic_create as topic_create
import examples.topic_delete as topic_delete
import examples.topic_message_submit as topic_message_submit
import examples.topic_update as topic_update
import examples.transaction_bytes_example as transaction_bytes_example
import examples.transfer_hbar as transfer_hbar
import examples.transfer_nft as transfer_nft
import examples.transfer_token as transfer_token

EXAMPLES_TO_RUN = [
    account_allowance_hbar,
    account_allowance_nft,
    account_create,
    account_delete,
    account_id,
    account_update,
    contract_create,
    contract_create_constructor,
    contract_create_with_bytecode,
    contract_delete,
    contract_execute,
    contract_execute_with_value,
    contract_update,
    custom_fee_fixed,
    custom_fee_fractional,
    custom_fee_royalty,
    ethereum_transaction_execute,
    file_append,
    file_create,
    file_delete,
    file_update,
    keys_private_der,
    keys_private_ecdsa,
    keys_private_ed25519,
    keys_public_der,
    keys_public_ecdsa,
    keys_public_ed25519,
    logging_example,
    prng_transaction,
    query_account_info,
    query_account_records,
    query_balance,
    query_contract_bytecode,
    query_contract_call,
    query_contract_info,
    query_file_contents,
    query_file_info,
    query_nft_info,
    query_payment,
    query_receipt,
    query_record,
    query_schedule_info,
    query_token_info_fungible,
    query_token_info_nft,
    query_topic_info,
    query_topic_message,
    revenue_generating_topics,
    schedule_account_create,
    schedule_delete,
    schedule_sign,
    token_airdrop,
    token_airdrop_cancel,
    token_airdrop_claim_signature_not_required_auto,
    token_airdrop_claim_signature_required,
    token_allowance,
    token_associate,
    token_burn_fungible,
    token_burn_nft,
    token_create_fungible_finite,
    token_create_fungible_infinite,
    token_create_nft_finite,
    token_create_nft_infinite,
    token_delete,
    token_dissociate,
    token_freeze,
    token_grant_kyc,
    token_mint_fungible,
    token_mint_non_fungible,
    token_pause,
    token_reject_fungible_token,
    token_reject_nft,
    token_revoke_kyc,
    token_unfreeze,
    token_unpause,
    token_update_fee_schedule_fungible,
    token_update_fee_schedule_nft,
    token_update_fungible,
    token_update_key,
    token_update_nft,
    token_update_nfts,
    token_wipe,
    topic_create,
    topic_delete,
    topic_message_submit,
    topic_update,
    transaction_bytes_example,
    transfer_hbar,
    transfer_nft,
    transfer_token,
]

SKIPPED_EXAMPLES = ['__init__.py', 'node_delete.py', 'node_update.py', 'node_create.py']
LOG_MODE = "all"
