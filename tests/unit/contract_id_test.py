from hiero_sdk_python.contract.contract_id import ContractId


def test_repr_numeric_contract_id():
    contract_id = ContractId(0, 0, 42)
    assert repr(contract_id) == "ContractId(shard=0, realm=0, contract=42)"


def test_repr_evm_contract_id():
    evm_address = bytes.fromhex("a" * 40)
    contract_id = ContractId(1, 2, evm_address=evm_address)
    assert repr(contract_id) == (
        f"ContractId(shard=1, realm=2, evm_address={evm_address.hex()})"
    )
