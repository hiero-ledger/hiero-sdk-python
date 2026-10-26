from __future__ import annotations

import dataclasses

import pytest

from hiero_sdk_python.account.mirror_node_token_balance import MirrorNodeTokenBalance
from hiero_sdk_python.tokens.token_id import TokenId


pytestmark = pytest.mark.unit


def json_response(token_id, balance, decimals=None):
    """Helper to create the token_balance mirrornode response."""
    return {"tokens": [{"balance": balance, "decimals": decimals, "token_id": f"{token_id}"}]}


# constructor


def test_constructor_with_params(token_id):
    """Test MirrorNodeTokenBalance constructor."""
    balance, decimals = 10, 1

    token_balance1 = MirrorNodeTokenBalance(token_id, balance, decimals)
    assert token_balance1 is not None
    assert token_balance1.token_id == token_id
    assert token_balance1.balance == balance
    assert token_balance1.decimals is not None
    assert token_balance1.decimals == decimals

    assert token_balance1.associated is True

    token_balance2 = MirrorNodeTokenBalance(token_id, balance, 0, associated=False)
    assert token_balance2.token_id == token_id
    assert token_balance2.balance == balance
    assert token_balance2.associated is False


def test_frozen(token_id):
    """Test MirrorNodeTokenBalance is immutable."""
    token_balance = MirrorNodeTokenBalance(token_id, 1, 0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        token_balance.balance = 2


@pytest.mark.parametrize("associated", [1, 0, "True", None, {}])
def test_constructor_with_invalid_associated(token_id, associated):
    """Test MirrorNodeTokenBalance constructor with non-bool associated raises error."""
    with pytest.raises(TypeError, match="associated must be a bool"):
        MirrorNodeTokenBalance(token_id, 1, 0, associated=associated)


@pytest.mark.parametrize("token_id", ["0.0.100", 101, 0.1, True, {}, [], None])
def test_constructor_with_invalid_token_id(token_id):
    """Test MirrorNodeTokenBalance constructor with invalid token_id raises error."""
    with pytest.raises(TypeError, match="token_id must be an instance of TokenId"):
        MirrorNodeTokenBalance(token_id, 1, 0)


@pytest.mark.parametrize("balance", ["100", 0.1, True, {}, [], None])
def test_constructor_with_invalid_balance(token_id, balance):
    """Test MirrorNodeTokenBalance constructor with invalid balance raises error."""
    with pytest.raises(TypeError, match="balance must be an integer"):
        MirrorNodeTokenBalance(token_id, balance, 0)


@pytest.mark.parametrize("decimals", ["100", 0.1, True, {}, [], None])
def test_constructor_with_invalid_decimals(token_id, decimals):
    """Test MirrorNodeTokenBalance constructor with invalid decimals raises error."""
    with pytest.raises(TypeError, match="decimals must be an integer"):
        MirrorNodeTokenBalance(token_id, 1, decimals)


# _from_json()


@pytest.mark.parametrize("requested_token_id", ["0.0.100", 101, 0.1, True, {}, [], None])
def test_from_json_with_invalid_token_id(requested_token_id):
    """Test from_json raises error when token_id type is invalid."""
    with pytest.raises(TypeError, match="requested_token_id must be of type TokenId"):
        MirrorNodeTokenBalance._from_json({}, requested_token_id)


@pytest.mark.parametrize("root", ["{}", 101, 0.1, True, [], None])
def test_from_json_with_invalid_root(token_id, root):
    """Test from_json raises error when root type is invalid."""
    with pytest.raises(TypeError, match="root must be a dictionary"):
        MirrorNodeTokenBalance._from_json(root, token_id)


def test_from_json_parses_json_response(token_id):
    """Test from_json correctly parse the json response."""
    balance, decimals = 10, 1

    response1 = json_response(str(token_id), balance, decimals)
    token_balance1 = MirrorNodeTokenBalance._from_json(response1, token_id)
    assert token_balance1 is not None
    assert token_balance1.token_id == token_id
    assert token_balance1.balance == balance
    assert token_balance1.decimals is not None
    assert token_balance1.decimals == decimals

    assert token_balance1.associated is True

    # decimals null -> 0, still associated
    response2 = json_response(str(token_id), balance)
    token_balance2 = MirrorNodeTokenBalance._from_json(response2, token_id)
    assert token_balance2 is not None
    assert token_balance2.token_id == token_id
    assert token_balance2.balance == balance
    assert token_balance2.decimals == 0
    assert token_balance2.associated is True


def test_from_json_empty_tokens_is_not_associated(token_id):
    """Test from_json maps an empty tokens array to a not-associated balance."""
    token_balance = MirrorNodeTokenBalance._from_json({"tokens": []}, token_id)

    assert token_balance.token_id == token_id
    assert token_balance.balance == 0
    assert token_balance.decimals == 0
    assert token_balance.associated is False


def test_from_json_missing_tokens_key_raises(token_id):
    """Test from_json raises ValueError when the tokens key is absent."""
    with pytest.raises(ValueError, match="missing tokens array"):
        MirrorNodeTokenBalance._from_json({}, token_id)


def test_from_json_null_tokens_raises(token_id):
    """Test from_json raises ValueError when tokens is null."""
    with pytest.raises(ValueError, match="missing tokens array"):
        MirrorNodeTokenBalance._from_json({"tokens": None}, token_id)


@pytest.mark.parametrize("balance", [2**53 + 1, 2**63 - 1])
def test_from_json_large_balance_round_trips_exactly(token_id, balance):
    """Test large integer balances are preserved exactly."""
    token_balance = MirrorNodeTokenBalance._from_json(json_response(token_id, balance, 2), token_id)
    assert type(token_balance.balance) is int
    assert token_balance.balance == balance


@pytest.mark.parametrize("balance", [10.0, "10", True])
def test_from_json_invalid_balance_type_raises(token_id, balance):
    """Test from_json rejects non-integer balances."""
    with pytest.raises(TypeError, match="balance must be an integer"):
        MirrorNodeTokenBalance._from_json(json_response(token_id, balance, 0), token_id)


@pytest.mark.parametrize("decimals", [True, 1.0, "1"])
def test_from_json_invalid_decimals_type_raises(token_id, decimals):
    """Test from_json rejects non-integer decimals."""
    with pytest.raises(TypeError, match="decimals must be an integer"):
        MirrorNodeTokenBalance._from_json(json_response(token_id, 1, decimals), token_id)


@pytest.mark.parametrize("tokens", ["[]", {"balance": 10}, 1, 0.1, True])
def test_from_json_malformed_tokens_fields(token_id, tokens):
    """Test from_json raise error for malformed tokens field."""
    response = {"tokens": tokens}
    with pytest.raises(TypeError, match="tokens must be a list"):
        MirrorNodeTokenBalance._from_json(response, token_id)


@pytest.mark.parametrize("token_balance", ["{}", None, 1, 0.1, True, []])
def test_from_json_malformed_token_relationship_fields(token_id, token_balance):
    """Test from_json raise error for malformed tokens field."""
    response = {"tokens": [token_balance]}
    with pytest.raises(TypeError, match="token relationship must be a dictionary"):
        MirrorNodeTokenBalance._from_json(response, token_id)


def test_from_json_override_requestion_token_id(token_id):
    """Test from_json override the requesting_token_id if response containing token_id."""
    response_token_id, balance = "0.0.100", 10
    response = json_response(response_token_id, balance)

    token_balance = MirrorNodeTokenBalance._from_json(response, token_id)
    assert token_balance is not None
    assert token_balance.token_id != token_id
    assert token_balance.token_id == TokenId.from_string(response_token_id)
    assert token_balance.balance == balance


def test_from_json_when_balance_is_none(token_id):
    """Test from_json parse balance as 0 if balance field is None"""
    response = json_response(token_id, None)

    token_balance = MirrorNodeTokenBalance._from_json(response, token_id)
    assert token_balance is not None
    assert token_balance.balance == 0
