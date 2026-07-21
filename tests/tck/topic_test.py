"""Test cases for the Hiero SDK TCK updateTopic handler."""

from __future__ import annotations

import importlib

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.token_id import TokenId
from tck.handlers import topic as topic_handlers
from tck.handlers.registry import get_handler
from tck.param.topic import UpdateTopicParams
from tck.util.key_utils import get_key_from_string


pytestmark = pytest.mark.unit


SAMPLE_KEY_HEX = (
    "30540201010420d0b3d3c266ad9aa414f41e3050d64f4012765abc94a745cbd0607bf41da51a96a"
    "00706052b8104000aa124032200037aa11171d538daf5c624f313bc106fff289e4a24768880d0fa71dd302a1fa9e7"
)


def full_params_dict():
    """Returns a fully populated updateTopic JSON-RPC params dict."""
    return {
        "sessionId": "session-abc-123",
        "topicId": "0.0.100",
        "memo": "Updated Memo",
        "adminKey": SAMPLE_KEY_HEX,
        "submitKey": SAMPLE_KEY_HEX,
        "autoRenewPeriod": "7776000",
        "autoRenewAccountId": "0.0.200",
        "expirationTime": "1700000000",
        "feeScheduleKey": SAMPLE_KEY_HEX,
        "feeExemptKeys": [SAMPLE_KEY_HEX],
        "customFees": [
            {
                "feeCollectorAccountId": "0.0.300",
                "feeCollectorsExempt": "true",
                "fixedFee": {"amount": "10", "denominatingTokenId": "0.0.400"},
            }
        ],
    }


# --- UpdateTopicParams.parse_json_params ------------------------------------


def test_parse_json_params_with_all_fields():
    """Test that all updateTopic fields parse from a full JSON-RPC params dict."""
    params = UpdateTopicParams.parse_json_params(full_params_dict())

    assert params.topicId == "0.0.100"
    assert params.memo == "Updated Memo"
    assert params.adminKey == SAMPLE_KEY_HEX
    assert params.submitKey == SAMPLE_KEY_HEX
    assert isinstance(params.autoRenewPeriod, int)
    assert params.autoRenewPeriod == 7776000
    assert params.autoRenewAccountId == "0.0.200"
    assert isinstance(params.expirationTime, int)
    assert params.expirationTime == 1700000000
    assert params.feeScheduleKey == SAMPLE_KEY_HEX
    assert params.feeExemptKeys == [SAMPLE_KEY_HEX]
    assert len(params.customFees) == 1
    assert params.customFees[0].feeCollectorAccountId == "0.0.300"
    assert params.customFees[0].feeCollectorsExempt is True
    assert params.customFees[0].fixedFee.amount == "10"
    assert params.customFees[0].fixedFee.denominatingTokenId == "0.0.400"
    assert params.sessionId == "session-abc-123"


def test_parse_json_params_with_minimal_fields():
    """Test that omitted optional fields parse as None."""
    params = UpdateTopicParams.parse_json_params({"sessionId": "s1", "topicId": "0.0.100"})

    assert params.topicId == "0.0.100"
    assert params.memo is None
    assert params.adminKey is None
    assert params.submitKey is None
    assert params.autoRenewPeriod is None
    assert params.autoRenewAccountId is None
    assert params.expirationTime is None
    assert params.feeScheduleKey is None
    assert params.feeExemptKeys is None
    assert params.customFees is None
    assert params.commonTransactionParams is None


def test_parse_json_params_invalid_fee_exempt_keys_type():
    """Test that a non-list feeExemptKeys raises ValueError."""
    with pytest.raises(ValueError, match="feeExemptKeys must be a list"):
        UpdateTopicParams.parse_json_params({"sessionId": "s1", "topicId": "0.0.100", "feeExemptKeys": "not-a-list"})


def test_parse_json_params_invalid_custom_fees_type():
    """Test that a non-list customFees raises ValueError."""
    with pytest.raises(ValueError, match="customFees must be a list"):
        UpdateTopicParams.parse_json_params({"sessionId": "s1", "topicId": "0.0.100", "customFees": "not-a-list"})


def test_parse_json_params_invalid_custom_fees_item_type():
    """Test that a customFees list with a non-dict item raises ValueError.

    Regression test: the item-type guard previously checked the outer list
    instead of each loop item, so it never actually validated item contents.
    """
    with pytest.raises(ValueError, match="each customFees item must be an object"):
        UpdateTopicParams.parse_json_params({"sessionId": "s1", "topicId": "0.0.100", "customFees": ["not-a-dict"]})


def test_parse_json_params_with_valid_custom_fees():
    """Test that a well-formed customFees list parses without raising.

    Regression test: the item-type guard used to raise on any non-empty
    customFees list, even one made entirely of valid objects.
    """
    params = UpdateTopicParams.parse_json_params(
        {
            "sessionId": "s1",
            "topicId": "0.0.100",
            "customFees": [{"feeCollectorAccountId": "0.0.300", "fixedFee": {"amount": "10"}}],
        }
    )

    assert len(params.customFees) == 1
    assert params.customFees[0].feeCollectorAccountId == "0.0.300"


# --- _build_update_topic_transaction -----------------------------------------


def test_build_update_topic_transaction_sets_all_provided_fields():
    """Test that every provided field is set on the built TopicUpdateTransaction."""
    params = UpdateTopicParams.parse_json_params(full_params_dict())

    transaction = topic_handlers._build_update_topic_transaction(params)

    assert transaction.topic_id == TopicId.from_string("0.0.100")
    assert transaction.memo == "Updated Memo"
    assert transaction.admin_key == get_key_from_string(SAMPLE_KEY_HEX)
    assert transaction.submit_key == get_key_from_string(SAMPLE_KEY_HEX)
    assert transaction.auto_renew_period == Duration(7776000)
    assert transaction.auto_renew_account == AccountId.from_string("0.0.200")
    assert transaction.expiration_time == Timestamp(1700000000, 0)
    assert transaction.fee_schedule_key == get_key_from_string(SAMPLE_KEY_HEX)
    assert transaction.fee_exempt_keys == [get_key_from_string(SAMPLE_KEY_HEX)]
    assert transaction.custom_fees == [
        CustomFixedFee(
            amount=10,
            fee_collector_account_id=AccountId.from_string("0.0.300"),
            denominating_token_id=TokenId.from_string("0.0.400"),
            all_collectors_are_exempt=True,
        )
    ]


def test_build_update_topic_transaction_leaves_omitted_fields_untouched():
    """Test the set-only-present-fields behavior when only topicId is given.

    auto_renew_period is asserted against TopicUpdateTransaction's own constructor
    default (Duration(7890000)), not None: unlike _build_update_account_transaction,
    this builder cannot reset it to None because
    TopicUpdateTransaction.set_auto_renew_period rejects None outright.
    """
    params = UpdateTopicParams.parse_json_params({"sessionId": "s1", "topicId": "0.0.100"})

    transaction = topic_handlers._build_update_topic_transaction(params)

    assert transaction.topic_id == TopicId.from_string("0.0.100")
    assert transaction.memo == ""
    assert transaction.admin_key is None
    assert transaction.submit_key is None
    assert transaction.auto_renew_period == Duration(7890000)
    assert transaction.auto_renew_account is None
    assert transaction.expiration_time is None
    assert transaction.fee_schedule_key is None
    assert transaction.fee_exempt_keys is None
    assert transaction.custom_fees is None


def test_build_update_topic_transaction_sets_topic_id():
    """Test topicId is set on the transaction when provided and left None when omitted."""
    with_id = UpdateTopicParams.parse_json_params({"sessionId": "s1", "topicId": "0.0.555"})
    without_id = UpdateTopicParams.parse_json_params({"sessionId": "s1"})

    assert topic_handlers._build_update_topic_transaction(with_id).topic_id == TopicId.from_string("0.0.555")
    assert topic_handlers._build_update_topic_transaction(without_id).topic_id is None


def test_build_update_topic_transaction_sets_expiration_time():
    """Test expirationTime is converted to a Timestamp with 0 nanos, and left None when omitted."""
    with_expiration = UpdateTopicParams.parse_json_params(
        {"sessionId": "s1", "topicId": "0.0.100", "expirationTime": "1700000000"}
    )
    without_expiration = UpdateTopicParams.parse_json_params({"sessionId": "s1", "topicId": "0.0.100"})

    transaction_with = topic_handlers._build_update_topic_transaction(with_expiration)
    transaction_without = topic_handlers._build_update_topic_transaction(without_expiration)

    assert transaction_with.expiration_time == Timestamp(1700000000, 0)
    assert transaction_without.expiration_time is None


# --- registry wiring ---------------------------------------------------------


def test_update_topic_registered_in_handler_registry():
    """Test that "updateTopic" resolves to the real update_topic function.

    Forces re-registration via importlib.reload first: tests/tck/handlers_test.py
    has an autouse fixture that clears the shared registry in its teardown, and
    since it collects/runs alphabetically before this file, the real handlers
    registered at import time would otherwise already be wiped by the time this
    test runs.
    """
    importlib.reload(topic_handlers)

    handler = get_handler("updateTopic")

    # rpc_method registers handle_sdk_errors(func) but binds the module-level
    # name to the original func, so unwrap the same way dispatch() does.
    assert getattr(handler, "__wrapped__", handler) is topic_handlers.update_topic
