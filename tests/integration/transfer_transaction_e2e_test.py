import pytest

from hiero_sdk_python.account.account_allowance_approve_transaction import (
    AccountAllowanceApproveTransaction,
)
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from tests.integration.utils import (
    IntegrationTestEnv,
    create_fungible_token,
    create_nft_token,
)


@pytest.mark.integration
def test_integration_transfer_transaction_can_transfer_hbar():
    env = IntegrationTestEnv()

    try:
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()

        initial_balance = Hbar(1)

        account_transaction = AccountCreateTransaction(
            key=new_account_public_key, initial_balance=initial_balance, memo="Recipient Account"
        )

        receipt = account_transaction.execute(env.client)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), f"Account creation failed with status: {ResponseCode(receipt.status).name}"

        account_id = receipt.account_id
        assert account_id is not None

        transfer_transaction = TransferTransaction()
        transfer_transaction.add_hbar_transfer(env.operator_id, -1)
        transfer_transaction.add_hbar_transfer(account_id, 1)

        receipt = transfer_transaction.execute(env.client)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), f"Transfer failed with status: {ResponseCode(receipt.status).name}"

        query_transaction = CryptoGetAccountBalanceQuery(account_id)
        balance = query_transaction.execute(env.client)

        expected_balance_tinybars = Hbar(1).to_tinybars() + 1
        assert (
            balance and balance.hbars.to_tinybars() == expected_balance_tinybars
        ), f"Expected balance: {expected_balance_tinybars}, actual balance: {balance.hbars.to_tinybars()}"
    finally:
        env.close()


@pytest.mark.integration
def test_integration_token_transfer_transaction_can_transfer_token():
    env = IntegrationTestEnv()

    try:
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()

        initial_balance = Hbar(1)

        account_transaction = AccountCreateTransaction(
            key=new_account_public_key, initial_balance=initial_balance, memo="Recipient Account"
        )

        receipt = account_transaction.execute(env.client)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), f"Account creation failed with status: {ResponseCode(receipt.status).name}"

        account_id = receipt.account_id
        assert account_id is not None

        token_id = create_fungible_token(env)
        assert token_id is not None

        associate_transaction = TokenAssociateTransaction(
            account_id=account_id, token_ids=[token_id]
        )

        associate_transaction.freeze_with(env.client)
        associate_transaction.sign(new_account_private_key)
        receipt = associate_transaction.execute(env.client)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), f"Token association failed with status: {ResponseCode(receipt.status).name}"

        transfer_transaction = TransferTransaction()
        transfer_transaction.add_token_transfer(token_id, env.operator_id, -1)
        transfer_transaction.add_token_transfer(token_id, account_id, 1)

        receipt = transfer_transaction.execute(env.client)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), f"Token transfer failed with status: {ResponseCode(receipt.status).name}"

        query_transaction = CryptoGetAccountBalanceQuery(account_id)
        balance = query_transaction.execute(env.client)

        assert balance is not None
    finally:
        env.close()


@pytest.mark.integration
def test_integration_token_transfer_transaction_can_transfer_nft():
    env = IntegrationTestEnv()

    try:
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()

        initial_balance = Hbar(1)

        account_transaction = AccountCreateTransaction(
            key=new_account_public_key, initial_balance=initial_balance, memo="Recipient Account"
        )

        receipt = account_transaction.execute(env.client)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), f"Account creation failed with status: {ResponseCode(receipt.status).name}"

        account_id = receipt.account_id
        assert account_id is not None

        token_id = create_nft_token(env)
        assert token_id is not None

        mint_transaction = TokenMintTransaction(token_id=token_id, metadata=[b"test"])

        receipt = mint_transaction.execute(env.client)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), f"NFT mint failed with status: {ResponseCode(receipt.status).name}"

        serial_number = receipt.serial_numbers[0]

        nft_id = NftId(token_id, serial_number)

        associate_transaction = TokenAssociateTransaction(
            account_id=account_id, token_ids=[token_id]
        )

        associate_transaction.freeze_with(env.client)
        associate_transaction.sign(new_account_private_key)
        receipt = associate_transaction.execute(env.client)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), f"NFT association failed with status: {ResponseCode(receipt.status).name}"

        transfer_transaction = TransferTransaction()
        transfer_transaction.add_nft_transfer(nft_id, env.operator_id, account_id)

        receipt = transfer_transaction.execute(env.client)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), f"NFT transfer failed with status: {ResponseCode(receipt.status).name}"

        query_transaction = CryptoGetAccountBalanceQuery(account_id)
        balance = query_transaction.execute(env.client)

        assert balance is not None, "Balance query returned None"
        assert balance.token_balances == {token_id: serial_number}, (
            f"Expected token_balances {{{token_id}: {serial_number}}}, "
            f"got {balance.token_balances}"
        )
    finally:
        env.close()


@pytest.mark.integration
def test_integration_transfer_transaction_transfer_hbar_nothing_set():
    env = IntegrationTestEnv()

    try:
        transfer_transaction = TransferTransaction()

        receipt = transfer_transaction.execute(env.client)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), f"Transfer failed with status: {ResponseCode(receipt.status).name}"
    finally:
        env.close()


@pytest.mark.integration
def test_integration_transfer_transaction_transfer_wrong_hbar_amount():
    env = IntegrationTestEnv()

    try:
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()

        initial_balance = Hbar(1)

        account_transaction = AccountCreateTransaction(
            key=new_account_public_key, initial_balance=initial_balance, memo="Recipient Account"
        )

        receipt = account_transaction.execute(env.client)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), f"Account creation failed with status: {ResponseCode(receipt.status).name}"

        account_id = receipt.account_id
        assert account_id is not None

        transfer_transaction = TransferTransaction()
        transfer_transaction.add_hbar_transfer(env.operator_id, -1)
        transfer_transaction.add_hbar_transfer(account_id, 2)

        with pytest.raises(
            PrecheckError, match=f"Transaction failed precheck with status: INVALID_ACCOUNT_AMOUNTS"
        ):
            transfer_transaction.execute(env.client)
    finally:
        env.close()


@pytest.mark.integration
def test_integration_transfer_transaction_transfer_hbar_fail_not_enough_balance():
    env = IntegrationTestEnv()

    try:
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()

        initial_balance = 1000

        account_transaction = AccountCreateTransaction(
            key=new_account_public_key, initial_balance=initial_balance, memo="Account 1"
        )

        receipt = account_transaction.execute(env.client)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), f"Account creation failed with status: {ResponseCode(receipt.status).name}"

        account_1_id = receipt.account_id
        assert account_1_id is not None

        transfer_transaction = TransferTransaction()
        transfer_transaction.add_hbar_transfer(account_1_id, -20000)
        transfer_transaction.add_hbar_transfer(env.operator_id, 20000)

        transfer_transaction.freeze_with(env.client)
        transfer_transaction.sign(new_account_private_key)
        receipt = transfer_transaction.execute(env.client)

        assert (
            receipt.status == ResponseCode.INSUFFICIENT_ACCOUNT_BALANCE
        ), f"Transfer should have failed with INSUFFICIENT_ACCOUNT_BALANCE status but got: {ResponseCode(receipt.status).name}"
    finally:
        env.close()


@pytest.mark.integration
def test_integration_token_transfer_transaction_fail_not_enough_balance():
    env = IntegrationTestEnv()

    try:
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()

        initial_balance = Hbar(1)

        account_transaction = AccountCreateTransaction(
            key=new_account_public_key, initial_balance=initial_balance, memo="Recipient Account"
        )

        receipt = account_transaction.execute(env.client)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), f"Account creation failed with status: {ResponseCode(receipt.status).name}"

        account_id = receipt.account_id
        assert account_id is not None

        token_id = create_fungible_token(env)
        assert token_id is not None

        associate_transaction = TokenAssociateTransaction(
            account_id=account_id, token_ids=[token_id]
        )

        associate_transaction.freeze_with(env.client)
        associate_transaction.sign(new_account_private_key)
        receipt = associate_transaction.execute(env.client)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), f"Token association failed with status: {ResponseCode(receipt.status).name}"

        transfer_transaction = TransferTransaction()
        transfer_transaction.add_token_transfer(token_id, env.operator_id, -100000)
        transfer_transaction.add_token_transfer(token_id, account_id, 100000)

        receipt = transfer_transaction.execute(env.client)

        assert (
            receipt.status == ResponseCode.INSUFFICIENT_TOKEN_BALANCE
        ), f"Token transfer should have failed with INSUFFICIENT_TOKEN_BALANCE status but got: {ResponseCode(receipt.status).name}"
    finally:
        env.close()


@pytest.mark.integration
def test_integration_token_transfer_transaction_fail_not_your_nft():
    env = IntegrationTestEnv()

    try:
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()

        initial_balance = Hbar(1)

        account_transaction = AccountCreateTransaction(
            key=new_account_public_key, initial_balance=initial_balance, memo="Recipient Account"
        )

        receipt = account_transaction.execute(env.client)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), f"Account creation failed with status: {ResponseCode(receipt.status).name}"

        account_id = receipt.account_id
        assert account_id is not None

        token_id = create_nft_token(env)
        assert token_id is not None

        mint_transaction = TokenMintTransaction(token_id=token_id, metadata=[b"test"])

        receipt = mint_transaction.execute(env.client)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), f"NFT mint failed with status: {ResponseCode(receipt.status).name}"

        serial_number = receipt.serial_numbers[0]

        nft_id = NftId(token_id, serial_number)

        associate_transaction = TokenAssociateTransaction(
            account_id=account_id, token_ids=[token_id]
        )

        associate_transaction.freeze_with(env.client)
        associate_transaction.sign(new_account_private_key)
        receipt = associate_transaction.execute(env.client)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), f"NFT association failed with status: {ResponseCode(receipt.status).name}"

        transfer_transaction = TransferTransaction()
        transfer_transaction.add_nft_transfer(nft_id, account_id, env.operator_id)

        transfer_transaction.freeze_with(env.client)
        transfer_transaction.sign(new_account_private_key)
        receipt = transfer_transaction.execute(env.client)

        assert (
            receipt.status == ResponseCode.SENDER_DOES_NOT_OWN_NFT_SERIAL_NO
        ), f"NFT transfer should have failed with SENDER_DOES_NOT_OWN_NFT_SERIAL_NO status but got: {ResponseCode(receipt.status).name}"
    finally:
        env.close()


@pytest.mark.integration
def test_integration_transfer_transaction_approved_token_transfer():
    env = IntegrationTestEnv()

    try:
        # Create new account
        account = env.create_account()

        # Create fungible token
        token_id = create_fungible_token(env)
        assert token_id is not None

        # Associate token with new account
        receipt = (
            TokenAssociateTransaction()
            .set_account_id(account.id)
            .add_token_id(token_id)
            .freeze_with(env.client)
            .sign(account.key)
            .execute(env.client)
        )

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), f"Token association failed with status: {ResponseCode(receipt.status).name}"

        # Test approved token transfer with decimals
        receipt = (
            AccountAllowanceApproveTransaction()
            .approve_token_allowance(token_id, env.operator_id, account.id, 500)
            .execute(env.client)
        )
        env.client.set_operator(account.id, account.key)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), f"Token allowance approval failed with status: {ResponseCode(receipt.status).name}"

        transfer_receipt = (
            TransferTransaction()
            .set_transaction_id(TransactionId.generate(account.id))
            .add_approved_token_transfer_with_decimals(token_id, account.id, 500, 2)
            .add_approved_token_transfer_with_decimals(token_id, env.operator_id, -499, 2)
            .add_token_transfer_with_decimals(token_id, account.id, -1, 2)
            .freeze_with(env.client)
            .sign(account.key)
            .execute(env.client)
        )
        assert (
            transfer_receipt.status == ResponseCode.SUCCESS
        ), f"Transfer failed with status: {ResponseCode(transfer_receipt.status).name}"

    finally:
        env.close()


@pytest.mark.integration
def test_integration_transfer_transaction_approved_nft_transfer():
    """Test NFT transfer with approval flag set to True."""
    env = IntegrationTestEnv()

    try:
        new_account_private_key = PrivateKey.generate()
        new_account_public_key = new_account_private_key.public_key()

        initial_balance = Hbar(10)

        account_transaction = AccountCreateTransaction(
            key=new_account_public_key, initial_balance=initial_balance, memo="Recipient Account"
        )

        receipt = account_transaction.execute(env.client)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), f"Account creation failed with status: {ResponseCode(receipt.status).name}"

        account_id = receipt.account_id
        assert account_id is not None

        token_id = create_nft_token(env)
        assert token_id is not None

        mint_transaction = TokenMintTransaction(token_id=token_id, metadata=[b"test"])

        receipt = mint_transaction.execute(env.client)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), f"NFT mint failed with status: {ResponseCode(receipt.status).name}"

        serial_number = receipt.serial_numbers[0]

        nft_id = NftId(token_id, serial_number)

        associate_transaction = TokenAssociateTransaction(
            account_id=account_id, token_ids=[token_id]
        )

        associate_transaction.freeze_with(env.client)
        associate_transaction.sign(new_account_private_key)
        receipt = associate_transaction.execute(env.client)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), f"NFT association failed with status: {ResponseCode(receipt.status).name}"

        allowance_receipt = (
            AccountAllowanceApproveTransaction()
            .approve_token_nft_allowance(nft_id, env.operator_id, account_id)
            .execute(env.client)
        )

        assert (
            allowance_receipt.status == ResponseCode.SUCCESS
        ), f"Allowance approval failed with status: {ResponseCode(allowance_receipt.status).name}"

        env.client.set_operator(account_id, new_account_private_key)

        transfer_transaction = TransferTransaction()
        transfer_transaction.set_transaction_id(TransactionId.generate(account_id))
        transfer_transaction.add_approved_nft_transfer(nft_id, env.operator_id, account_id)
        transfer_transaction.freeze_with(env.client)
        transfer_transaction.sign(new_account_private_key)

        receipt = transfer_transaction.execute(env.client)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), f"NFT transfer failed with status: {ResponseCode(receipt.status).name}"

        query_transaction = CryptoGetAccountBalanceQuery(account_id)
        balance = query_transaction.execute(env.client)

        assert balance is not None, "Balance query returned None"
        assert balance.token_balances == {token_id: serial_number}, (
            f"Expected token_balances {{{token_id}: {serial_number}}}, "
            f"got {balance.token_balances}"
        )
    finally:
        env.close()
