from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.crypto.private_key import PrivateKey


def main():
  client = Client.from_env()
  tx = AccountCreateTransaction().set_key_without_alias(PrivateKey.generate()).freeze_with(client)


  print(tx.get_size())
  print(tx.get_body_size())


if __name__ == "__main__":
  main()
