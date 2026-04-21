from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.consensus.topic_message_submit_transaction import TopicMessageSubmitTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey


def main() -> None:
    client = Client.from_env()
    tx = (
        AccountCreateTransaction()
        .set_key(PrivateKey.generate())
        .set_node_account_id(AccountId(0, 0, 3))
        .freeze_with(client)
    )
    print(tx.size)
    print(tx.body_size)

    tx2 = (
        TopicMessageSubmitTransaction()
        .set_topic_id(TopicId.from_string("0.0.23"))
        .set_message("A" * 1300)
        .freeze_with(client)
    )
    print(tx2.size)
    print(tx2.body_size)
    print(tx2.body_size_all_chunks)


if __name__ == "__main__":
    main()
