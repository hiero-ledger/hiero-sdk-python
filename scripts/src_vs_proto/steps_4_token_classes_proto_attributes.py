# Auto-generated proto attributes and setters

proto_mappings = {
    'AccountAmount': {
        'attributes': [
            'accountID',
            'amount',
            'is_approval',
            'pre_tx_allowance_hook',
            'pre_post_tx_allowance_hook',
        ],
        'setters': [
            'set_accountID',
            'set_amount',
            'set_is_approval',
            'set_pre_tx_allowance_hook',
            'set_pre_post_tx_allowance_hook',
        ]
    },
    'AccountID': {
        'attributes': [
            'shardNum',
            'realmNum',
            'accountNum',
            'alias',
        ],
        'setters': [
            'set_shardNum',
            'set_realmNum',
            'set_accountNum',
            'set_alias',
        ]
    },
    'AssessedCustomFee': {
        'attributes': [
            'amount',
            'token_id',
            'fee_collector_account_id',
            'effective_payer_account_id',
        ],
        'setters': [
            'set_amount',
            'set_token_id',
            'set_fee_collector_account_id',
            'set_effective_payer_account_id',
        ]
    },
    'AtomicBatchTransactionBody': {
        'attributes': [
            'transactions',
        ],
        'setters': [
            'set_transactions',
        ]
    },
    'ContractID': {
        'attributes': [
            'shardNum',
            'realmNum',
            'contractNum',
            'evm_address',
        ],
        'setters': [
            'set_shardNum',
            'set_realmNum',
            'set_contractNum',
            'set_evm_address',
        ]
    },
    'CurrentAndNextFeeSchedule': {
        'attributes': [
            'currentFeeSchedule',
            'nextFeeSchedule',
        ],
        'setters': [
            'set_currentFeeSchedule',
            'set_nextFeeSchedule',
        ]
    },
    'CustomFee': {
        'attributes': [
            'fixed_fee',
            'fractional_fee',
            'royalty_fee',
            'fee_collector_account_id',
            'all_collectors_are_exempt',
        ],
        'setters': [
            'set_fixed_fee',
            'set_fractional_fee',
            'set_royalty_fee',
            'set_fee_collector_account_id',
            'set_all_collectors_are_exempt',
        ]
    },
    'CustomFeeLimit': {
        'attributes': [
            'account_id',
            'fees',
        ],
        'setters': [
            'set_account_id',
            'set_fees',
        ]
    },
    'EvmHookCall': {
        'attributes': [
            'data',
            'gas_limit',
        ],
        'setters': [
            'set_data',
            'set_gas_limit',
        ]
    },
    'FeeComponents': {
        'attributes': [
            'min',
            'max',
            'constant',
            'bpt',
            'vpt',
            'rbh',
            'sbh',
            'gas',
            'tv',
            'bpr',
            'sbpr',
        ],
        'setters': [
            'set_min',
            'set_max',
            'set_constant',
            'set_bpt',
            'set_vpt',
            'set_rbh',
            'set_sbh',
            'set_gas',
            'set_tv',
            'set_bpr',
            'set_sbpr',
        ]
    },
    'FeeData': {
        'attributes': [
            'nodedata',
            'networkdata',
            'servicedata',
            'subType',
        ],
        'setters': [
            'set_nodedata',
            'set_networkdata',
            'set_servicedata',
            'set_subType',
        ]
    },
    'FeeExemptKeyList': {
        'attributes': [
            'keys',
        ],
        'setters': [
            'set_keys',
        ]
    },
    'FeeSchedule': {
        'attributes': [
            'transactionFeeSchedule',
            'expiryTime',
        ],
        'setters': [
            'set_transactionFeeSchedule',
            'set_expiryTime',
        ]
    },
    'FileID': {
        'attributes': [
            'shardNum',
            'realmNum',
            'fileNum',
        ],
        'setters': [
            'set_shardNum',
            'set_realmNum',
            'set_fileNum',
        ]
    },
    'FixedCustomFee': {
        'attributes': [
            'fixed_fee',
            'fee_collector_account_id',
        ],
        'setters': [
            'set_fixed_fee',
            'set_fee_collector_account_id',
        ]
    },
    'FixedCustomFeeList': {
        'attributes': [
            'fees',
        ],
        'setters': [
            'set_fees',
        ]
    },
    'FixedFee': {
        'attributes': [
            'amount',
            'denominating_token_id',
        ],
        'setters': [
            'set_amount',
            'set_denominating_token_id',
        ]
    },
    'Fraction': {
        'attributes': [
            'numerator',
            'denominator',
        ],
        'setters': [
            'set_numerator',
            'set_denominator',
        ]
    },
    'FractionalFee': {
        'attributes': [
            'fractional_amount',
            'minimum_amount',
            'maximum_amount',
            'net_of_transfers',
        ],
        'setters': [
            'set_fractional_amount',
            'set_minimum_amount',
            'set_maximum_amount',
            'set_net_of_transfers',
        ]
    },
    'HookCall': {
        'attributes': [
            'full_hook_id',
            'hook_id',
            'evm_hook_call',
        ],
        'setters': [
            'set_full_hook_id',
            'set_hook_id',
            'set_evm_hook_call',
        ]
    },
    'HookEntityId': {
        'attributes': [
            'account_id',
        ],
        'setters': [
            'set_account_id',
        ]
    },
    'HookId': {
        'attributes': [
            'entity_id',
            'hook_id',
        ],
        'setters': [
            'set_entity_id',
            'set_hook_id',
        ]
    },
    'Key': {
        'attributes': [
            'contractID',
            'ed25519',
            'RSA_3072',
            'ECDSA_384',
            'thresholdKey',
            'keyList',
            'ECDSA_secp256k1',
            'delegatable_contract_id',
        ],
        'setters': [
            'set_contractID',
            'set_ed25519',
            'set_RSA_3072',
            'set_ECDSA_384',
            'set_thresholdKey',
            'set_keyList',
            'set_ECDSA_secp256k1',
            'set_delegatable_contract_id',
        ]
    },
    'KeyList': {
        'attributes': [
            'keys',
        ],
        'setters': [
            'set_keys',
        ]
    },
    'NftID': {
        'attributes': [
            'token_ID',
            'serial_number',
        ],
        'setters': [
            'set_token_ID',
            'set_serial_number',
        ]
    },
    'NftTransfer': {
        'attributes': [
            'senderAccountID',
            'receiverAccountID',
            'serialNumber',
            'is_approval',
            'pre_tx_sender_allowance_hook',
            'pre_post_tx_sender_allowance_hook',
            'pre_tx_receiver_allowance_hook',
            'pre_post_tx_receiver_allowance_hook',
        ],
        'setters': [
            'set_senderAccountID',
            'set_receiverAccountID',
            'set_serialNumber',
            'set_is_approval',
            'set_pre_tx_sender_allowance_hook',
            'set_pre_post_tx_sender_allowance_hook',
            'set_pre_tx_receiver_allowance_hook',
            'set_pre_post_tx_receiver_allowance_hook',
        ]
    },
    'NodeAddress': {
        'attributes': [
            'ipAddress',
            'portno',
            'memo',
            'RSA_PubKey',
            'nodeId',
            'nodeAccountId',
            'nodeCertHash',
            'serviceEndpoint',
            'description',
            'stake',
        ],
        'setters': [
            'set_ipAddress',
            'set_portno',
            'set_memo',
            'set_RSA_PubKey',
            'set_nodeId',
            'set_nodeAccountId',
            'set_nodeCertHash',
            'set_serviceEndpoint',
            'set_description',
            'set_stake',
        ]
    },
    'NodeAddressBook': {
        'attributes': [
            'nodeAddress',
        ],
        'setters': [
            'set_nodeAddress',
        ]
    },
    'PendingAirdropId': {
        'attributes': [
            'sender_id',
            'receiver_id',
            'fungible_token_type',
            'non_fungible_token',
        ],
        'setters': [
            'set_sender_id',
            'set_receiver_id',
            'set_fungible_token_type',
            'set_non_fungible_token',
        ]
    },
    'PendingAirdropRecord': {
        'attributes': [
            'pending_airdrop_id',
            'pending_airdrop_value',
        ],
        'setters': [
            'set_pending_airdrop_id',
            'set_pending_airdrop_value',
        ]
    },
    'PendingAirdropValue': {
        'attributes': [
            'amount',
        ],
        'setters': [
            'set_amount',
        ]
    },
    'RealmID': {
        'attributes': [
            'shardNum',
            'realmNum',
        ],
        'setters': [
            'set_shardNum',
            'set_realmNum',
        ]
    },
    'RoyaltyFee': {
        'attributes': [
            'exchange_value_fraction',
            'fallback_fee',
        ],
        'setters': [
            'set_exchange_value_fraction',
            'set_fallback_fee',
        ]
    },
    'ScheduleID': {
        'attributes': [
            'shardNum',
            'realmNum',
            'scheduleNum',
        ],
        'setters': [
            'set_shardNum',
            'set_realmNum',
            'set_scheduleNum',
        ]
    },
    'SemanticVersion': {
        'attributes': [
            'major',
            'minor',
            'patch',
            'pre',
            'build',
        ],
        'setters': [
            'set_major',
            'set_minor',
            'set_patch',
            'set_pre',
            'set_build',
        ]
    },
    'ServiceEndpoint': {
        'attributes': [
            'ipAddressV4',
            'port',
            'domain_name',
        ],
        'setters': [
            'set_ipAddressV4',
            'set_port',
            'set_domain_name',
        ]
    },
    'ServicesConfigurationList': {
        'attributes': [
            'nameValue',
        ],
        'setters': [
            'set_nameValue',
        ]
    },
    'Setting': {
        'attributes': [
            'name',
            'value',
            'data',
        ],
        'setters': [
            'set_name',
            'set_value',
            'set_data',
        ]
    },
    'ShardID': {
        'attributes': [
            'shardNum',
        ],
        'setters': [
            'set_shardNum',
        ]
    },
    'Signature': {
        'attributes': [
            'contract',
            'ed25519',
            'RSA_3072',
            'ECDSA_384',
            'thresholdSignature',
            'signatureList',
        ],
        'setters': [
            'set_contract',
            'set_ed25519',
            'set_RSA_3072',
            'set_ECDSA_384',
            'set_thresholdSignature',
            'set_signatureList',
        ]
    },
    'SignatureList': {
        'attributes': [
            'sigs',
        ],
        'setters': [
            'set_sigs',
        ]
    },
    'SignatureMap': {
        'attributes': [
            'sigPair',
        ],
        'setters': [
            'set_sigPair',
        ]
    },
    'SignaturePair': {
        'attributes': [
            'pubKeyPrefix',
            'contract',
            'ed25519',
            'RSA_3072',
            'ECDSA_384',
            'ECDSA_secp256k1',
        ],
        'setters': [
            'set_pubKeyPrefix',
            'set_contract',
            'set_ed25519',
            'set_RSA_3072',
            'set_ECDSA_384',
            'set_ECDSA_secp256k1',
        ]
    },
    'StakingInfo': {
        'attributes': [
            'decline_reward',
            'stake_period_start',
            'pending_reward',
            'staked_to_me',
            'staked_account_id',
            'staked_node_id',
        ],
        'setters': [
            'set_decline_reward',
            'set_stake_period_start',
            'set_pending_reward',
            'set_staked_to_me',
            'set_staked_account_id',
            'set_staked_node_id',
        ]
    },
    'ThresholdKey': {
        'attributes': [
            'threshold',
            'keys',
        ],
        'setters': [
            'set_threshold',
            'set_keys',
        ]
    },
    'ThresholdSignature': {
        'attributes': [
            'sigs',
        ],
        'setters': [
            'set_sigs',
        ]
    },
    'Timestamp': {
        'attributes': [
            'seconds',
            'nanos',
        ],
        'setters': [
            'set_seconds',
            'set_nanos',
        ]
    },
    'TimestampSeconds': {
        'attributes': [
            'seconds',
        ],
        'setters': [
            'set_seconds',
        ]
    },
    'TokenAirdropTransactionBody': {
        'attributes': [
            'token_transfers',
        ],
        'setters': [
            'set_token_transfers',
        ]
    },
    'TokenAssociateTransactionBody': {
        'attributes': [
            'account',
            'tokens',
        ],
        'setters': [
            'set_account',
            'set_tokens',
        ]
    },
    'TokenAssociation': {
        'attributes': [
            'token_id',
            'account_id',
        ],
        'setters': [
            'set_token_id',
            'set_account_id',
        ]
    },
    'TokenBalance': {
        'attributes': [
            'tokenId',
            'balance',
            'decimals',
        ],
        'setters': [
            'set_tokenId',
            'set_balance',
            'set_decimals',
        ]
    },
    'TokenBalances': {
        'attributes': [
            'tokenBalances',
        ],
        'setters': [
            'set_tokenBalances',
        ]
    },
    'TokenBurnTransactionBody': {
        'attributes': [
            'token',
            'amount',
            'serialNumbers',
        ],
        'setters': [
            'set_token',
            'set_amount',
            'set_serialNumbers',
        ]
    },
    'TokenCancelAirdropTransactionBody': {
        'attributes': [
            'pending_airdrops',
        ],
        'setters': [
            'set_pending_airdrops',
        ]
    },
    'TokenCreateTransactionBody': {
        'attributes': [
            'name',
            'symbol',
            'decimals',
            'initialSupply',
            'treasury',
            'adminKey',
            'kycKey',
            'freezeKey',
            'wipeKey',
            'supplyKey',
            'freezeDefault',
            'expiry',
            'autoRenewAccount',
            'autoRenewPeriod',
            'memo',
            'tokenType',
            'supplyType',
            'maxSupply',
            'fee_schedule_key',
            'custom_fees',
            'pause_key',
            'metadata',
            'metadata_key',
        ],
        'setters': [
            'set_name',
            'set_symbol',
            'set_decimals',
            'set_initialSupply',
            'set_treasury',
            'set_adminKey',
            'set_kycKey',
            'set_freezeKey',
            'set_wipeKey',
            'set_supplyKey',
            'set_freezeDefault',
            'set_expiry',
            'set_autoRenewAccount',
            'set_autoRenewPeriod',
            'set_memo',
            'set_tokenType',
            'set_supplyType',
            'set_maxSupply',
            'set_fee_schedule_key',
            'set_custom_fees',
            'set_pause_key',
            'set_metadata',
            'set_metadata_key',
        ]
    },
    'TokenDeleteTransactionBody': {
        'attributes': [
            'token',
        ],
        'setters': [
            'set_token',
        ]
    },
    'TokenDissociateTransactionBody': {
        'attributes': [
            'account',
            'tokens',
        ],
        'setters': [
            'set_account',
            'set_tokens',
        ]
    },
    'TokenFeeScheduleUpdateTransactionBody': {
        'attributes': [
            'token_id',
            'custom_fees',
        ],
        'setters': [
            'set_token_id',
            'set_custom_fees',
        ]
    },
    'TokenFreezeAccountTransactionBody': {
        'attributes': [
            'token',
            'account',
        ],
        'setters': [
            'set_token',
            'set_account',
        ]
    },
    'TokenGetInfoQuery': {
        'attributes': [
            'header',
            'token',
        ],
        'setters': [
            'set_header',
            'set_token',
        ]
    },
    'TokenGetInfoResponse': {
        'attributes': [
            'header',
            'tokenInfo',
        ],
        'setters': [
            'set_header',
            'set_tokenInfo',
        ]
    },
    'TokenGetNftInfoQuery': {
        'attributes': [
            'header',
            'nftID',
        ],
        'setters': [
            'set_header',
            'set_nftID',
        ]
    },
    'TokenGetNftInfoResponse': {
        'attributes': [
            'header',
            'nft',
        ],
        'setters': [
            'set_header',
            'set_nft',
        ]
    },
    'TokenGrantKycTransactionBody': {
        'attributes': [
            'token',
            'account',
        ],
        'setters': [
            'set_token',
            'set_account',
        ]
    },
    'TokenID': {
        'attributes': [
            'shardNum',
            'realmNum',
            'tokenNum',
        ],
        'setters': [
            'set_shardNum',
            'set_realmNum',
            'set_tokenNum',
        ]
    },
    'TokenInfo': {
        'attributes': [
            'tokenId',
            'name',
            'symbol',
            'decimals',
            'totalSupply',
            'treasury',
            'adminKey',
            'kycKey',
            'freezeKey',
            'wipeKey',
            'supplyKey',
            'defaultFreezeStatus',
            'defaultKycStatus',
            'deleted',
            'autoRenewAccount',
            'autoRenewPeriod',
            'expiry',
            'memo',
            'tokenType',
            'supplyType',
            'maxSupply',
            'fee_schedule_key',
            'custom_fees',
            'pause_key',
            'pause_status',
            'ledger_id',
            'metadata',
            'metadata_key',
        ],
        'setters': [
            'set_tokenId',
            'set_name',
            'set_symbol',
            'set_decimals',
            'set_totalSupply',
            'set_treasury',
            'set_adminKey',
            'set_kycKey',
            'set_freezeKey',
            'set_wipeKey',
            'set_supplyKey',
            'set_defaultFreezeStatus',
            'set_defaultKycStatus',
            'set_deleted',
            'set_autoRenewAccount',
            'set_autoRenewPeriod',
            'set_expiry',
            'set_memo',
            'set_tokenType',
            'set_supplyType',
            'set_maxSupply',
            'set_fee_schedule_key',
            'set_custom_fees',
            'set_pause_key',
            'set_pause_status',
            'set_ledger_id',
            'set_metadata',
            'set_metadata_key',
        ]
    },
    'TokenMintTransactionBody': {
        'attributes': [
            'token',
            'amount',
            'metadata',
        ],
        'setters': [
            'set_token',
            'set_amount',
            'set_metadata',
        ]
    },
    'TokenNftInfo': {
        'attributes': [
            'nftID',
            'accountID',
            'creationTime',
            'metadata',
            'ledger_id',
            'spender_id',
        ],
        'setters': [
            'set_nftID',
            'set_accountID',
            'set_creationTime',
            'set_metadata',
            'set_ledger_id',
            'set_spender_id',
        ]
    },
    'TokenPauseTransactionBody': {
        'attributes': [
            'token',
        ],
        'setters': [
            'set_token',
        ]
    },
    'TokenRelationship': {
        'attributes': [
            'tokenId',
            'symbol',
            'balance',
            'kycStatus',
            'freezeStatus',
            'decimals',
            'automatic_association',
        ],
        'setters': [
            'set_tokenId',
            'set_symbol',
            'set_balance',
            'set_kycStatus',
            'set_freezeStatus',
            'set_decimals',
            'set_automatic_association',
        ]
    },
    'TokenRevokeKycTransactionBody': {
        'attributes': [
            'token',
            'account',
        ],
        'setters': [
            'set_token',
            'set_account',
        ]
    },
    'TokenTransferList': {
        'attributes': [
            'token',
            'transfers',
            'nftTransfers',
            'expected_decimals',
        ],
        'setters': [
            'set_token',
            'set_transfers',
            'set_nftTransfers',
            'set_expected_decimals',
        ]
    },
    'TokenUnfreezeAccountTransactionBody': {
        'attributes': [
            'token',
            'account',
        ],
        'setters': [
            'set_token',
            'set_account',
        ]
    },
    'TokenUpdateNftsTransactionBody': {
        'attributes': [
            'token',
            'serial_numbers',
            'metadata',
        ],
        'setters': [
            'set_token',
            'set_serial_numbers',
            'set_metadata',
        ]
    },
    'TokenUpdateTransactionBody': {
        'attributes': [
            'token',
            'symbol',
            'name',
            'treasury',
            'adminKey',
            'kycKey',
            'freezeKey',
            'wipeKey',
            'supplyKey',
            'autoRenewAccount',
            'autoRenewPeriod',
            'expiry',
            'memo',
            'fee_schedule_key',
            'pause_key',
            'metadata',
            'metadata_key',
            'key_verification_mode',
        ],
        'setters': [
            'set_token',
            'set_symbol',
            'set_name',
            'set_treasury',
            'set_adminKey',
            'set_kycKey',
            'set_freezeKey',
            'set_wipeKey',
            'set_supplyKey',
            'set_autoRenewAccount',
            'set_autoRenewPeriod',
            'set_expiry',
            'set_memo',
            'set_fee_schedule_key',
            'set_pause_key',
            'set_metadata',
            'set_metadata_key',
            'set_key_verification_mode',
        ]
    },
    'TokenWipeAccountTransactionBody': {
        'attributes': [
            'token',
            'account',
            'amount',
            'serialNumbers',
        ],
        'setters': [
            'set_token',
            'set_account',
            'set_amount',
            'set_serialNumbers',
        ]
    },
    'TopicID': {
        'attributes': [
            'shardNum',
            'realmNum',
            'topicNum',
        ],
        'setters': [
            'set_shardNum',
            'set_realmNum',
            'set_topicNum',
        ]
    },
    'Transaction': {
        'attributes': [
            'body',
            'sigs',
            'sigMap',
            'bodyBytes',
            'signedTransactionBytes',
        ],
        'setters': [
            'set_body',
            'set_sigs',
            'set_sigMap',
            'set_bodyBytes',
            'set_signedTransactionBytes',
        ]
    },
    'TransactionBody': {
        'attributes': [
            'transactionID',
            'nodeAccountID',
            'transactionFee',
            'transactionValidDuration',
            'generateRecord',
            'memo',
            'batch_key',
            'contractCall',
            'contractCreateInstance',
            'contractUpdateInstance',
            'cryptoAddLiveHash',
            'cryptoCreateAccount',
            'cryptoDelete',
            'cryptoDeleteLiveHash',
            'cryptoTransfer',
            'cryptoUpdateAccount',
            'fileAppend',
            'fileCreate',
            'fileDelete',
            'fileUpdate',
            'systemDelete',
            'systemUndelete',
            'contractDeleteInstance',
            'freeze',
            'consensusCreateTopic',
            'consensusUpdateTopic',
            'consensusDeleteTopic',
            'consensusSubmitMessage',
            'uncheckedSubmit',
            'tokenCreation',
            'tokenFreeze',
            'tokenUnfreeze',
            'tokenGrantKyc',
            'tokenRevokeKyc',
            'tokenDeletion',
            'tokenUpdate',
            'tokenMint',
            'tokenBurn',
            'tokenWipe',
            'tokenAssociate',
            'tokenDissociate',
            'scheduleCreate',
            'scheduleDelete',
            'scheduleSign',
            'token_fee_schedule_update',
            'token_pause',
            'token_unpause',
            'cryptoApproveAllowance',
            'cryptoDeleteAllowance',
            'ethereumTransaction',
            'node_stake_update',
            'util_prng',
            'token_update_nfts',
            'nodeCreate',
            'nodeUpdate',
            'nodeDelete',
            'tokenReject',
            'tokenAirdrop',
            'tokenCancelAirdrop',
            'tokenClaimAirdrop',
            'state_signature_transaction',
            'hints_preprocessing_vote',
            'hints_key_publication',
            'hints_partial_signature',
            'history_proof_signature',
            'history_proof_key_publication',
            'history_proof_vote',
            'crs_publication',
            'atomic_batch',
            'lambda_sstore',
            'hook_dispatch',
            'max_custom_fees',
        ],
        'setters': [
            'set_transactionID',
            'set_nodeAccountID',
            'set_transactionFee',
            'set_transactionValidDuration',
            'set_generateRecord',
            'set_memo',
            'set_batch_key',
            'set_contractCall',
            'set_contractCreateInstance',
            'set_contractUpdateInstance',
            'set_cryptoAddLiveHash',
            'set_cryptoCreateAccount',
            'set_cryptoDelete',
            'set_cryptoDeleteLiveHash',
            'set_cryptoTransfer',
            'set_cryptoUpdateAccount',
            'set_fileAppend',
            'set_fileCreate',
            'set_fileDelete',
            'set_fileUpdate',
            'set_systemDelete',
            'set_systemUndelete',
            'set_contractDeleteInstance',
            'set_freeze',
            'set_consensusCreateTopic',
            'set_consensusUpdateTopic',
            'set_consensusDeleteTopic',
            'set_consensusSubmitMessage',
            'set_uncheckedSubmit',
            'set_tokenCreation',
            'set_tokenFreeze',
            'set_tokenUnfreeze',
            'set_tokenGrantKyc',
            'set_tokenRevokeKyc',
            'set_tokenDeletion',
            'set_tokenUpdate',
            'set_tokenMint',
            'set_tokenBurn',
            'set_tokenWipe',
            'set_tokenAssociate',
            'set_tokenDissociate',
            'set_scheduleCreate',
            'set_scheduleDelete',
            'set_scheduleSign',
            'set_token_fee_schedule_update',
            'set_token_pause',
            'set_token_unpause',
            'set_cryptoApproveAllowance',
            'set_cryptoDeleteAllowance',
            'set_ethereumTransaction',
            'set_node_stake_update',
            'set_util_prng',
            'set_token_update_nfts',
            'set_nodeCreate',
            'set_nodeUpdate',
            'set_nodeDelete',
            'set_tokenReject',
            'set_tokenAirdrop',
            'set_tokenCancelAirdrop',
            'set_tokenClaimAirdrop',
            'set_state_signature_transaction',
            'set_hints_preprocessing_vote',
            'set_hints_key_publication',
            'set_hints_partial_signature',
            'set_history_proof_signature',
            'set_history_proof_key_publication',
            'set_history_proof_vote',
            'set_crs_publication',
            'set_atomic_batch',
            'set_lambda_sstore',
            'set_hook_dispatch',
            'set_max_custom_fees',
        ]
    },
    'TransactionFeeSchedule': {
        'attributes': [
            'hederaFunctionality',
            'feeData',
            'fees',
        ],
        'setters': [
            'set_hederaFunctionality',
            'set_feeData',
            'set_fees',
        ]
    },
    'TransactionID': {
        'attributes': [
            'transactionValidStart',
            'accountID',
            'scheduled',
            'nonce',
        ],
        'setters': [
            'set_transactionValidStart',
            'set_accountID',
            'set_scheduled',
            'set_nonce',
        ]
    },
    'TransactionRecord': {
        'attributes': [
            'receipt',
            'transactionHash',
            'consensusTimestamp',
            'transactionID',
            'memo',
            'transactionFee',
            'contractCallResult',
            'contractCreateResult',
            'transferList',
            'tokenTransferLists',
            'scheduleRef',
            'assessed_custom_fees',
            'automatic_token_associations',
            'parent_consensus_timestamp',
            'alias',
            'ethereum_hash',
            'paid_staking_rewards',
            'prng_bytes',
            'prng_number',
            'evm_address',
            'new_pending_airdrops',
        ],
        'setters': [
            'set_receipt',
            'set_transactionHash',
            'set_consensusTimestamp',
            'set_transactionID',
            'set_memo',
            'set_transactionFee',
            'set_contractCallResult',
            'set_contractCreateResult',
            'set_transferList',
            'set_tokenTransferLists',
            'set_scheduleRef',
            'set_assessed_custom_fees',
            'set_automatic_token_associations',
            'set_parent_consensus_timestamp',
            'set_alias',
            'set_ethereum_hash',
            'set_paid_staking_rewards',
            'set_prng_bytes',
            'set_prng_number',
            'set_evm_address',
            'set_new_pending_airdrops',
        ]
    },
    'TransferList': {
        'attributes': [
            'accountAmounts',
        ],
        'setters': [
            'set_accountAmounts',
        ]
    },
}

# Auto-generated proto enums

proto_enums = {
}
