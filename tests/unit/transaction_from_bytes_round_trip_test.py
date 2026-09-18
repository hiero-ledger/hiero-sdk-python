from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_allowance_approve_transaction import (
    AccountAllowanceApproveTransaction,
)
from hiero_sdk_python.account.account_allowance_delete_transaction import (
    AccountAllowanceDeleteTransaction,
)
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.account.account_delete_transaction import AccountDeleteTransaction
from hiero_sdk_python.account.account_update_transaction import AccountUpdateTransaction
from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.consensus.topic_delete_transaction import TopicDeleteTransaction
from hiero_sdk_python.consensus.topic_message_submit_transaction import (
    TopicMessageSubmitTransaction,
)
from hiero_sdk_python.consensus.topic_update_transaction import TopicUpdateTransaction
from hiero_sdk_python.contract.contract_create_transaction import ContractCreateTransaction
from hiero_sdk_python.contract.contract_delete_transaction import ContractDeleteTransaction
from hiero_sdk_python.contract.contract_execute_transaction import ContractExecuteTransaction
from hiero_sdk_python.contract.contract_update_transaction import ContractUpdateTransaction
from hiero_sdk_python.contract.ethereum_transaction import EthereumTransaction
from hiero_sdk_python.file.file_append_transaction import FileAppendTransaction
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.file.file_delete_transaction import FileDeleteTransaction
from hiero_sdk_python.file.file_update_transaction import FileUpdateTransaction
from hiero_sdk_python.nodes.node_create_transaction import NodeCreateTransaction
from hiero_sdk_python.nodes.node_delete_transaction import NodeDeleteTransaction
from hiero_sdk_python.nodes.node_update_transaction import NodeUpdateTransaction
from hiero_sdk_python.nodes.registered_node_create_transaction import (
    RegisteredNodeCreateTransaction,
)
from hiero_sdk_python.nodes.registered_node_delete_transaction import (
    RegisteredNodeDeleteTransaction,
)
from hiero_sdk_python.nodes.registered_node_update_transaction import (
    RegisteredNodeUpdateTransaction,
)
from hiero_sdk_python.prng_transaction import PrngTransaction
from hiero_sdk_python.schedule.schedule_create_transaction import ScheduleCreateTransaction
from hiero_sdk_python.schedule.schedule_delete_transaction import ScheduleDeleteTransaction
from hiero_sdk_python.schedule.schedule_sign_transaction import ScheduleSignTransaction
from hiero_sdk_python.system.freeze_transaction import FreezeTransaction
from hiero_sdk_python.tokens.token_airdrop_claim import TokenClaimAirdropTransaction
from hiero_sdk_python.tokens.token_airdrop_transaction import TokenAirdropTransaction
from hiero_sdk_python.tokens.token_airdrop_transaction_cancel import (
    TokenCancelAirdropTransaction,
)
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_burn_transaction import TokenBurnTransaction
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_delete_transaction import TokenDeleteTransaction
from hiero_sdk_python.tokens.token_dissociate_transaction import TokenDissociateTransaction
from hiero_sdk_python.tokens.token_fee_schedule_update_transaction import (
    TokenFeeScheduleUpdateTransaction,
)
from hiero_sdk_python.tokens.token_freeze_transaction import TokenFreezeTransaction
from hiero_sdk_python.tokens.token_grant_kyc_transaction import TokenGrantKycTransaction
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.tokens.token_pause_transaction import TokenPauseTransaction
from hiero_sdk_python.tokens.token_reject_transaction import TokenRejectTransaction
from hiero_sdk_python.tokens.token_revoke_kyc_transaction import TokenRevokeKycTransaction
from hiero_sdk_python.tokens.token_unfreeze_transaction import TokenUnfreezeTransaction
from hiero_sdk_python.tokens.token_unpause_transaction import TokenUnpauseTransaction
from hiero_sdk_python.tokens.token_update_nfts_transaction import TokenUpdateNftsTransaction
from hiero_sdk_python.tokens.token_update_transaction import TokenUpdateTransaction
from hiero_sdk_python.tokens.token_wipe_transaction import TokenWipeTransaction
from hiero_sdk_python.transaction.batch_transaction import BatchTransaction
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction


pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "transaction_type, expected_class",
    [
        ("cryptoTransfer", TransferTransaction),
        ("contractCall", ContractExecuteTransaction),
        ("contractCreateInstance", ContractCreateTransaction),
        ("contractUpdateInstance", ContractUpdateTransaction),
        ("contractDeleteInstance", ContractDeleteTransaction),
        ("ethereumTransaction", EthereumTransaction),
        ("cryptoApproveAllowance", AccountAllowanceApproveTransaction),
        ("cryptoDeleteAllowance", AccountAllowanceDeleteTransaction),
        ("cryptoCreateAccount", AccountCreateTransaction),
        ("cryptoDelete", AccountDeleteTransaction),
        ("cryptoUpdateAccount", AccountUpdateTransaction),
        ("fileAppend", FileAppendTransaction),
        ("fileCreate", FileCreateTransaction),
        ("fileDelete", FileDeleteTransaction),
        ("fileUpdate", FileUpdateTransaction),
        ("freeze", FreezeTransaction),
        ("consensusCreateTopic", TopicCreateTransaction),
        ("consensusUpdateTopic", TopicUpdateTransaction),
        ("consensusDeleteTopic", TopicDeleteTransaction),
        ("consensusSubmitMessage", TopicMessageSubmitTransaction),
        ("tokenCreation", TokenCreateTransaction),
        ("tokenFreeze", TokenFreezeTransaction),
        ("tokenUnfreeze", TokenUnfreezeTransaction),
        ("tokenGrantKyc", TokenGrantKycTransaction),
        ("tokenRevokeKyc", TokenRevokeKycTransaction),
        ("tokenDeletion", TokenDeleteTransaction),
        ("tokenUpdate", TokenUpdateTransaction),
        ("tokenMint", TokenMintTransaction),
        ("tokenBurn", TokenBurnTransaction),
        ("tokenWipe", TokenWipeTransaction),
        ("tokenAssociate", TokenAssociateTransaction),
        ("tokenDissociate", TokenDissociateTransaction),
        ("token_pause", TokenPauseTransaction),
        ("token_unpause", TokenUnpauseTransaction),
        ("scheduleCreate", ScheduleCreateTransaction),
        ("scheduleDelete", ScheduleDeleteTransaction),
        ("scheduleSign", ScheduleSignTransaction),
        ("token_update_nfts", TokenUpdateNftsTransaction),
        ("token_fee_schedule_update", TokenFeeScheduleUpdateTransaction),
        ("nodeCreate", NodeCreateTransaction),
        ("nodeUpdate", NodeUpdateTransaction),
        ("nodeDelete", NodeDeleteTransaction),
        ("registeredNodeCreate", RegisteredNodeCreateTransaction),
        ("registeredNodeUpdate", RegisteredNodeUpdateTransaction),
        ("registeredNodeDelete", RegisteredNodeDeleteTransaction),
        ("util_prng", PrngTransaction),
        ("tokenReject", TokenRejectTransaction),
        ("tokenAirdrop", TokenAirdropTransaction),
        ("tokenClaimAirdrop", TokenClaimAirdropTransaction),
        ("tokenCancelAirdrop", TokenCancelAirdropTransaction),
        ("atomic_batch", BatchTransaction),
    ],
)
def test_get_transaction_class(transaction_type, expected_class):
    actual_class = Transaction._get_transaction_class(transaction_type)

    assert actual_class is expected_class


@pytest.mark.parametrize(
    "transaction_type",
    [
        "cryptoAddLiveHash",
        "cryptoDeleteLiveHash",
        "systemDelete",
        "systemUndelete",
    ],
)
def test_get_transaction_class_returns_none_for_unsupported_types(transaction_type):
    assert Transaction._get_transaction_class(transaction_type) is None


def test_get_transaction_class_returns_none_for_unknown_type():
    assert Transaction._get_transaction_class("unknownTransaction") is None
