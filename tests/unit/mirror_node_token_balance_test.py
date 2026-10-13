from __future__ import annotations

import pytest

from hiero_sdk_python.account.mirror_node_token_balance import MirrorNodeTokenBalance
from hiero_sdk_python.tokens.token_id import TokenId


pytestmark = pytest.mark.unit


def json_response(token_id, balance, decimals=None, associated=False):
    """Helper to create the token_balance mirrornode response."""
    return {
        "tokens": [
            {"automatic_association": associated, "balance": balance, "decimals": decimals, "token_id": token_id}
        ]
    }


# constructor


def test_constructor_with_params(token_id):
    """Test MirrorNodeTokenBalance constructor."""
    balance, decimals, associated = 10, 1, True

    token_balance1 = MirrorNodeTokenBalance(token_id, balance, decimals, associated)
    assert token_balance1 is not None
    assert token_balance1.token_id == token_id
    assert token_balance1.balance == balance
    assert token_balance1.decimals is not None
    assert token_balance1.decimals == decimals
    assert token_balance1.associated == associated

    # decimals as None

    token_balance2 = MirrorNodeTokenBalance(token_id, balance, None, associated)
    assert token_balance2 is not None
    assert token_balance2.token_id == token_id
    assert token_balance2.balance == balance
    assert token_balance2.decimals is None
    assert token_balance2.associated == associated


@pytest.mark.parametrize("token_id", ["0.0.100", 101, 0.1, True, {}, [], None])
def test_constructor_with_invalid_token_id(token_id):
    """Test MirrorNodeTokenBalance constructor with invalid token_id raises error."""
    with pytest.raises(TypeError, match="token_id must be an instance of TokenId"):
        MirrorNodeTokenBalance(token_id, 1, None, False)


@pytest.mark.parametrize("balance", ["100", 0.1, True, {}, [], None])
def test_constructor_with_invalid_balance(token_id, balance):
    """Test MirrorNodeTokenBalance constructor with invalid balance raises error."""
    with pytest.raises(TypeError, match="balance must be an integer"):
        MirrorNodeTokenBalance(token_id, balance, None, False)


@pytest.mark.parametrize("decimals", ["100", 0.1, True, {}, []])
def test_constructor_with_invalid_decimals(token_id, decimals):
    """Test MirrorNodeTokenBalance constructor with invalid decimals raises error."""
    with pytest.raises(TypeError, match="decimals must be an integer or None"):
        MirrorNodeTokenBalance(token_id, 1, decimals, False)


@pytest.mark.parametrize("associated", ["100", 1, 0.1, None, {}, []])
def test_constructor_with_invalid_associated(token_id, associated):
    """Test MirrorNodeTokenBalance constructor with invalid associated raises error."""
    with pytest.raises(TypeError, match="associated must be a boolean"):
        MirrorNodeTokenBalance(token_id, 1, None, associated)


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
    balance, decimals, associated = 10, 1, True

    response1 = json_response(str(token_id), balance, decimals, associated)
    token_balance1 = MirrorNodeTokenBalance._from_json(response1, token_id)
    assert token_balance1 is not None
    assert token_balance1.token_id == token_id
    assert token_balance1.balance == balance
    assert token_balance1.decimals is not None
    assert token_balance1.decimals == decimals
    assert token_balance1.associated == associated

    # decimal as None ans associated as False
    response2 = json_response(str(token_id), balance)
    token_balance2 = MirrorNodeTokenBalance._from_json(response2, token_id)
    assert token_balance2 is not None
    assert token_balance2.token_id == token_id
    assert token_balance2.balance == balance
    assert token_balance2.decimals is None
    assert token_balance2.associated is False


@pytest.mark.parametrize("tokens", [[], None])
def test_from_json_parse_empyt_and_null_tokens_field(token_id, tokens):
    """Test from_json parse None and empty tokens field and return not associated token_balance."""
    response = {"tokens": tokens}
    token_balance = MirrorNodeTokenBalance._from_json(response, token_id)

    assert token_balance is not None
    assert token_balance.token_id == token_id
    assert token_balance.balance == 0
    assert token_balance.decimals is None
    assert token_balance.associated is False


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
