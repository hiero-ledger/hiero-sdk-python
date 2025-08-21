import os
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
)
from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenType
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.custom_fractional_fee import CustomFractionalFee
from hiero_sdk_python.tokens.fee_assessment_method import FeeAssessmentMethod
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_fee_schedule_update_transaction import TokenFeeScheduleUpdateTransaction

load_dotenv()

def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network='testnet')
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
    client.set_operator(operator_id, operator_key)
    return client, operator_id, operator_key


def _initial_custom_fees(operator_id: AccountId):
    return [
        CustomFixedFee(
            amount=5,
            fee_collector_account_id=operator_id,
            all_collectors_are_exempt=False,
        ),
        CustomFractionalFee(
            numerator=1,
            denominator=20,  # 5%
            min_amount=1,
            max_amount=50,
            assessment_method=FeeAssessmentMethod.INCLUSIVE,
            fee_collector_account_id=operator_id,
            all_collectors_are_exempt=False,
        ),
    ]


def _updated_custom_fees(operator_id: AccountId):
    return [
        CustomFixedFee(
            amount=10,
            fee_collector_account_id=operator_id,
            all_collectors_are_exempt=False,
        ),
        CustomFractionalFee(
            numerator=3,
            denominator=100,  # 3%
            min_amount=2,
            max_amount=100,
            assessment_method=FeeAssessmentMethod.EXCLUSIVE,
            fee_collector_account_id=operator_id,
            all_collectors_are_exempt=True,
        ),
        CustomFixedFee(
            amount=1,
            fee_collector_account_id=operator_id,
            all_collectors_are_exempt=True,
        ),
    ]


def _is_success(receipt) -> bool:
    return receipt.status == ResponseCode.SUCCESS


def create_fungible_token_with_custom_fees(client, operator_id, operator_key):
    """Create a fungible token with initial custom fees and fee schedule key"""
    receipt = (
        TokenCreateTransaction()
        .set_token_name("MyExampleFT")
        .set_token_symbol("EXFT")
        .set_decimals(2)
        .set_initial_supply(1000)
        .set_treasury_account_id(operator_id)
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(10000)
        .set_admin_key(operator_key)
        .set_supply_key(operator_key)
        .set_custom_fees(_initial_custom_fees(operator_id))
        .execute(client)
    )

    if not _is_success(receipt):
        print(f"Fungible token creation failed with status: {ResponseCode(receipt.status).name}")
        return None

    token_id = receipt.token_id
    print(f"Fungible token created with ID: {token_id}")
    return token_id


def _print_fee(index: int, fee) -> None:
    print(f"  Fee {index}:")
    amount = getattr(fee, "amount", None)
    numerator = getattr(fee, "numerator", None)
    denominator = getattr(fee, "denominator", None)
    min_amount = getattr(fee, "min_amount", None)
    max_amount = getattr(fee, "max_amount", None)
    assessment_method = getattr(fee, "assessment_method", None)
    fee_collector = getattr(fee, "fee_collector_account_id", None)
    exempt = getattr(fee, "all_collectors_are_exempt", None)
    denom_token = getattr(fee, "denominating_token_id", None)

    if amount is not None:
        print("    Type: Fixed Fee")
        print(f"    Amount: {amount}")
        print(f"    Denominating Token: {denom_token if denom_token else 'HBAR'}")
    elif numerator is not None and denominator:
        print("    Type: Fractional Fee")
        print(f"    Fraction: {numerator}/{denominator}")
        if min_amount is not None:
            print(f"    Min Amount: {min_amount}")
        if max_amount is not None:
            print(f"    Max Amount: {max_amount}")
        if assessment_method is not None:
            print(f"    Assessment Method: {assessment_method}")
    else:
        print("    Type: Unknown")

    if fee_collector is not None:
        print(f"    Fee Collector: {fee_collector}")
    if exempt is not None:
        print(f"    All Collectors Exempt: {exempt}")


def get_token_info(client, token_id):
    """Get and display token information including custom fees"""
    token_info = TokenInfoQuery().set_token_id(token_id).execute(client)

    print(f"Token Name: {token_info.name}")
    print(f"Token Symbol: {token_info.symbol}")
    print(f"Custom Fees Count: {len(token_info.custom_fees)}")

    for i, fee in enumerate(token_info.custom_fees, start=1):
        _print_fee(i, fee)

    return token_info


def update_fee_schedule(client, token_id, operator_id, operator_key):
    """Update the token's fee schedule with new custom fees"""
    receipt = (
        TokenFeeScheduleUpdateTransaction()
        .set_token_id(token_id)
        .set_custom_fees(_updated_custom_fees(operator_id))
        .freeze_with(client)
        .sign(operator_key)
        .execute(client)
    )

    if not _is_success(receipt):
        print(f"Token fee schedule update failed with status: {ResponseCode(receipt.status).name}")
        if receipt.status == ResponseCode.TOKEN_HAS_NO_FEE_SCHEDULE_KEY:
            print("Note: This token was not created with a fee schedule key, so fee schedule updates are not allowed.")
        return False

    print("Successfully updated token fee schedule")
    return True


def clear_fee_schedule(client, token_id, operator_key):
    """Clear all custom fees from the token"""
    receipt = (
        TokenFeeScheduleUpdateTransaction()
        .set_token_id(token_id)
        .set_custom_fees([])
        .freeze_with(client)
        .sign(operator_key)
        .execute(client)
    )

    if not _is_success(receipt):
        print(f"Token fee schedule clear failed with status: {ResponseCode(receipt.status).name}")
        return False

    print("Successfully cleared all custom fees from token")
    return True


def token_fee_schedule_update():
    """
    Demonstrates the token fee schedule update functionality by:
    1. Setting up client with operator account
    2. Creating a fungible token with initial custom fees
    3. Displaying initial token info and custom fees
    4. Attempting to update the fee schedule (may fail if no fee schedule key)
    5. Clearing all custom fees from the token
    6. Displaying final token info
    """
    client, operator_id, operator_key = setup_client()

    token_id = create_fungible_token_with_custom_fees(client, operator_id, operator_key)
    if token_id is None:
        return

    print("\nToken info with initial custom fees:")
    get_token_info(client, token_id)

    print("\nAttempting to update fee schedule...")
    if not update_fee_schedule(client, token_id, operator_id, operator_key):
        print("\nFee schedule update failed. This is expected if the token was created without a fee schedule key.")
        print("Custom fees were set during token creation, but cannot be modified after creation without a fee schedule key.")
        return

    print("\nToken info after fee schedule update:")
    get_token_info(client, token_id)

    print("\nClearing all custom fees...")
    if clear_fee_schedule(client, token_id, operator_key):
        print("\nToken info after clearing custom fees:")
        get_token_info(client, token_id)


if __name__ == "__main__":
    token_fee_schedule_update()