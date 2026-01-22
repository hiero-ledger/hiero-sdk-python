
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.contract.contract_id import ContractId


def main():
  client = Client.from_env()
  contract_id = ContractId.from_string("0.0.000000000000000000000000000000000075a034")

  print(contract_id.to_evm_address())
  contract_id.populate_contract_num(client)


if __name__ == "__main__":
  main()