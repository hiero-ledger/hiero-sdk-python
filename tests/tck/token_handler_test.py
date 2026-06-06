"""Tests for token handlers required by the allowance-delete TCK suite."""

from __future__ import annotations

import pytest

from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.custom_fractional_fee import CustomFractionalFee
from hiero_sdk_python.tokens.custom_royalty_fee import CustomRoyaltyFee
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_type import TokenType
from tck.handlers.token import (
    _build_associate_token_transaction,
    _build_create_token_transaction,
    _build_delete_token_transaction,
    _build_freeze_token_transaction,
    _build_mint_token_transaction,
    _build_pause_token_transaction,
)
from tck.param.token import (
    AssociateTokenParams,
    CreateTokenParams,
    DeleteTokenParams,
    FreezeTokenParams,
    MintTokenParams,
    PauseTokenParams,
)


pytestmark = pytest.mark.unit

SESSION_ID = "token-test"


def test_build_create_nft_for_allowance_setup():
    supply_key = PrivateKey.generate_ed25519().to_string_der()
    params = CreateTokenParams.parse_json_params(
        {
            "sessionId": SESSION_ID,
            "name": "Allowance NFT",
            "symbol": "ANFT",
            "treasuryAccountId": "0.0.1001",
            "tokenType": "nft",
            "supplyKey": supply_key,
        }
    )

    transaction = _build_create_token_transaction(params)
    body = transaction._build_proto_body()

    assert body.name == "Allowance NFT"
    assert body.symbol == "ANFT"
    assert body.treasury.accountNum == 1001
    assert body.tokenType == TokenType.NON_FUNGIBLE_UNIQUE.value
    assert body.HasField("supplyKey")


def test_build_create_fungible_token_for_allowance_error_case():
    params = CreateTokenParams.parse_json_params(
        {
            "sessionId": SESSION_ID,
            "name": "Allowance FT",
            "symbol": "AFT",
            "treasuryAccountId": "0.0.1001",
            "tokenType": "ft",
            "initialSupply": "1000",
        }
    )

    body = _build_create_token_transaction(params)._build_proto_body()

    assert body.tokenType == TokenType.FUNGIBLE_COMMON.value
    assert body.initialSupply == 1000
    assert body.supplyType == SupplyType.INFINITE.value


def test_build_create_token_custom_fees():
    params = CreateTokenParams.parse_json_params(
        {
            "sessionId": SESSION_ID,
            "name": "Fee Token",
            "symbol": "FEE",
            "treasuryAccountId": "0.0.1001",
            "initialSupply": "1000",
            "customFees": [
                {
                    "feeCollectorAccountId": "0.0.1002",
                    "feeCollectorsExempt": True,
                    "fixedFee": {"amount": "1"},
                },
                {
                    "feeCollectorAccountId": "0.0.1002",
                    "feeCollectorsExempt": False,
                    "fractionalFee": {
                        "numerator": "1",
                        "denominator": "10",
                        "minimumAmount": "1",
                        "maximumAmount": "10",
                        "assessmentMethod": "exclusive",
                    },
                },
                {
                    "feeCollectorAccountId": "0.0.1002",
                    "feeCollectorsExempt": False,
                    "royaltyFee": {
                        "numerator": "1",
                        "denominator": "10",
                        "fallbackFee": {"amount": "2"},
                    },
                },
            ],
        }
    )

    fees = _build_create_token_transaction(params)._token_params.custom_fees

    assert isinstance(fees[0], CustomFixedFee)
    assert fees[0].all_collectors_are_exempt is True
    assert isinstance(fees[1], CustomFractionalFee)
    assert fees[1].assessment_method.value == 1
    assert isinstance(fees[2], CustomRoyaltyFee)
    assert fees[2].fallback_fee.amount == 2


def test_build_mint_and_associate_transactions_for_allowance_setup():
    mint_params = MintTokenParams.parse_json_params(
        {
            "sessionId": SESSION_ID,
            "tokenId": "0.0.2001",
            "metadata": ["1234"],
        }
    )
    associate_params = AssociateTokenParams.parse_json_params(
        {
            "sessionId": SESSION_ID,
            "accountId": "0.0.1002",
            "tokenIds": ["0.0.2001", "0.0.2002"],
        }
    )

    mint_body = _build_mint_token_transaction(mint_params)._build_proto_body()
    associate_body = _build_associate_token_transaction(associate_params)._build_proto_body()

    assert mint_body.token.tokenNum == 2001
    assert list(mint_body.metadata) == [bytes.fromhex("1234")]
    assert associate_body.account.accountNum == 1002
    assert [token.tokenNum for token in associate_body.tokens] == [2001, 2002]


def test_build_delete_freeze_and_pause_transactions_for_allowance_cases():
    delete_transaction = _build_delete_token_transaction(
        DeleteTokenParams.parse_json_params(
            {
                "sessionId": SESSION_ID,
                "tokenId": "0.0.2001",
            }
        )
    )
    freeze_transaction = _build_freeze_token_transaction(
        FreezeTokenParams.parse_json_params(
            {
                "sessionId": SESSION_ID,
                "tokenId": "0.0.2001",
                "accountId": "0.0.1001",
            }
        )
    )
    pause_transaction = _build_pause_token_transaction(
        PauseTokenParams.parse_json_params(
            {
                "sessionId": SESSION_ID,
                "tokenId": "0.0.2001",
            }
        )
    )

    assert delete_transaction.token_id.num == 2001
    assert freeze_transaction.token_id.num == 2001
    assert freeze_transaction.account_id.num == 1001
    assert pause_transaction.token_id.num == 2001


@pytest.mark.parametrize(
    ("params_type", "payload", "message"),
    [
        (MintTokenParams, {"metadata": "1234"}, "metadata must be a list"),
        (AssociateTokenParams, {"tokenIds": "0.0.2001"}, "tokenIds must be a list"),
        (CreateTokenParams, {"customFees": {}}, "customFees must be a list"),
    ],
)
def test_token_parameter_shapes_are_validated(params_type, payload, message):
    with pytest.raises(ValueError, match=message):
        params_type.parse_json_params({"sessionId": SESSION_ID, **payload})
