from pytest import fixture, mark
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_pause_transaction import TokenPauseTransaction
from hiero_sdk_python.tokens.token_unpause_transaction import TokenUnpauseTransaction
from tests.integration.utils_for_test import env, create_fungible_token

pause_key = PrivateKey.generate()

@fixture
def pausable_token(env):
    return create_fungible_token(
        env, 
        opts=[lambda tx: tx.set_pause_key(pause_key)]
    )

def pause_token(env, token_id):
    token_pasue_tx = (
        TokenPauseTransaction()
        .set_token_id(token_id)
        .freeze_with(env.client)
        .sign(pause_key)
    )

    return token_pasue_tx.execute(env.client)


def test_integration_token_unpause_transaction(env, pausable_token):
    pause_tx_recipt = pause_token(env, pausable_token)
        
    assert pause_tx_recipt.status == ResponseCode.SUCCESS

    info1 = TokenInfoQuery().set_token_id(pausable_token).execute(env.client)
    assert info1.pause_status.name == "PAUSED"

    token_unpause_tx = (
        TokenUnpauseTransaction()
        .set_token_id(pausable_token)
        .freeze_with(env.client)
        .sign(pause_key)
    )

    unpause_tx_recipt = token_unpause_tx.execute(env.client)
    assert unpause_tx_recipt.status == ResponseCode.SUCCESS

    info2 = TokenInfoQuery().set_token_id(pausable_token).execute(env.client)
    assert info2.pause_status.name == "UNPAUSED"
