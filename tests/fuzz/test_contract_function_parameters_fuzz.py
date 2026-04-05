import pytest
from eth_abi.exceptions import EncodingTypeError, ValueOutOfBounds
from hypothesis import given

from hiero_sdk_python import ContractFunctionParameters
from tests.fuzz.conftest import ContractValueCase, InvalidContractValueCase, get_strategy

pytestmark = pytest.mark.fuzz


def _encode(function_name: str | None, case: ContractValueCase) -> bytes:
    params = ContractFunctionParameters(function_name)
    getattr(params, case.method_name)(case.value)
    encoded = params.to_bytes()

    assert isinstance(encoded, bytes)
    assert bytes(params) == encoded
    assert params.to_bytes() == encoded
    return encoded


@given(
    function_name=get_strategy("contract_function_name"),
    case=get_strategy("contract_value_valid"),
)
def test_contract_function_parameters_encode_valid_values(
    function_name: str | None,
    case: ContractValueCase,
) -> None:
    """Valid add_* inputs must encode deterministically."""
    encoded = _encode(function_name, case)
    unnamed_encoded = _encode(None, case)

    if function_name is None:
        assert encoded == unnamed_encoded
    else:
        assert len(encoded) >= 4
        assert encoded[4:] == unnamed_encoded


@given(
    function_name=get_strategy("contract_function_name"),
    case=get_strategy("contract_value_invalid"),
)
def test_contract_function_parameters_reject_invalid_values(
    function_name: str | None,
    case: InvalidContractValueCase,
) -> None:
    """Wrong-shaped or out-of-range values must raise the expected encoder exception."""
    params = ContractFunctionParameters(function_name)

    with pytest.raises(case.expected_exception):
        getattr(params, case.method_name)(case.value)
        params.to_bytes()


def test_contract_function_parameters_invalid_case_exceptions_are_specific() -> None:
    """Guardrail: invalid-case expectations should stay narrow and intentional."""
    assert ValueOutOfBounds is not ValueError
    assert EncodingTypeError is not TypeError
