import base64
import os

import requests
from dotenv import load_dotenv

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.consensus.topic_message_submit_transaction import TopicMessageSubmitTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.file.file_append_transaction import FileAppendTransaction
from hiero_sdk_python.file.file_contents_query import FileContentsQuery
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.transaction.transaction_id import TransactionId


load_dotenv()
submitKey = PrivateKey.from_string_der(os.getenv("SECONDARY_KEY"))

client = Client.from_env()


def test1():
    tx = (
        AccountCreateTransaction()
        .set_key_without_alias(PrivateKey.generate_ed25519())
        .set_account_memo("test serialization")
        .set_initial_balance(1)
    )
    str = base64.b64encode(tx.to_bytes()).decode()

    response = requests.post(
        "http://localhost:8080",
        json={"transaction": str},
    )

    print(response.json())


def test2():
    tx = (
        AccountCreateTransaction()
        .set_key_without_alias(PrivateKey.generate_ed25519())
        .set_account_memo("test serialization freeze")
        .set_initial_balance(1)
        .set_node_account_ids(
            [AccountId.from_string("0.0.3"), AccountId.from_string("0.0.4"), AccountId.from_string("0.0.2")]
        )
        .set_transaction_id(TransactionId.generate(client.operator_account_id))
    ).freeze()
    str = base64.b64encode(tx.to_bytes()).decode()

    response = requests.post(
        "http://localhost:8080",
        json={"transaction": str},
    )

    print(response.json())


def test3():
    tx = (
        AccountCreateTransaction()
        .set_key_without_alias(PrivateKey.generate_ed25519())
        .set_account_memo("test serialization freeze client")
        .set_initial_balance(1)
    ).freeze_with(client)
    str = base64.b64encode(tx.to_bytes()).decode()

    response = requests.post(
        "http://localhost:8080",
        json={"transaction": str},
    )

    print(response.json())


def test4():
    tx = TopicMessageSubmitTransaction().set_topic_id(TopicId.from_string("0.0.10719576")).set_message("hello world")

    str = base64.b64encode(tx.to_bytes()).decode()

    response = requests.post(
        "http://localhost:8080",
        json={"transaction": str},
    )
    print(response)


def test5():
    tx = TopicMessageSubmitTransaction().set_topic_id(TopicId.from_string("0.0.10719576")).set_message("V" * 1025)

    str = base64.b64encode(tx.to_bytes()).decode()

    response = requests.post(
        "http://localhost:8080",
        json={"transaction": str},
    )
    print(response)


def test6():
    tx = (
        TopicMessageSubmitTransaction().set_topic_id(TopicId.from_string("0.0.10719576")).set_message("q" * 1025)
    ).freeze_with(client)

    str = base64.b64encode(tx.to_bytes()).decode()

    response = requests.post(
        "http://localhost:8080",
        json={"transaction": str},
        timeout=30,
    )
    print(response)


def test7():
    tx = (
        TopicMessageSubmitTransaction()
        .set_topic_id(TopicId.from_string("0.0.10719576"))
        .set_message("q" * 1025)
        .set_node_account_ids(
            [AccountId.from_string("0.0.3"), AccountId.from_string("0.0.4"), AccountId.from_string("0.0.2")]
        )
        .set_transaction_id(TransactionId.generate(client.operator_account_id))
    ).freeze()

    str = base64.b64encode(tx.to_bytes()).decode()

    response = requests.post(
        "http://localhost:8080",
        json={"transaction": str},
        timeout=30,
    )
    print(response)


def test8():
    tx = (
        TopicMessageSubmitTransaction()
        .set_topic_id(TopicId.from_string("0.0.10719576"))
        .set_message("hello_world")
        .set_node_account_ids(
            [AccountId.from_string("0.0.3"), AccountId.from_string("0.0.4"), AccountId.from_string("0.0.2")]
        )
        .set_transaction_id(TransactionId.generate(client.operator_account_id))
    ).freeze()

    str = base64.b64encode(tx.to_bytes()).decode()

    response = requests.post(
        "http://localhost:8080",
        json={"transaction": str},
        timeout=30,
    )
    print(response)


def test9():
    tx = (
        TopicMessageSubmitTransaction()
        .set_topic_id(TopicId.from_string("0.0.10765413"))
        .set_message("hello world")
        .set_node_account_ids(
            [AccountId.from_string("0.0.3"), AccountId.from_string("0.0.4"), AccountId.from_string("0.0.2")]
        )
        .set_transaction_id(TransactionId.generate(client.operator_account_id))
    ).freeze()
    tx.sign(submitKey)

    str = base64.b64encode(tx.to_bytes()).decode()

    response = requests.post(
        "http://localhost:8080",
        json={"transaction": str},
        timeout=30,
    )
    print(response)


def test10():
    tx = (
        TopicMessageSubmitTransaction()
        .set_topic_id(TopicId.from_string("0.0.10765413"))
        .set_message("h" * 1025)
        .set_node_account_ids(
            [AccountId.from_string("0.0.3"), AccountId.from_string("0.0.4"), AccountId.from_string("0.0.2")]
        )
        .set_transaction_id(TransactionId.generate(client.operator_account_id))
    ).freeze()
    tx.sign(submitKey)

    str = base64.b64encode(tx.to_bytes()).decode()

    response = requests.post(
        "http://localhost:8080",
        json={"transaction": str},
        timeout=30,
    )
    print(response)


def test11():
    tx = (
        TopicMessageSubmitTransaction().set_topic_id(TopicId.from_string("0.0.10765413")).set_message("d" * 1025)
    ).freeze_with(client)
    tx.sign(submitKey)

    str = base64.b64encode(tx.to_bytes()).decode()

    response = requests.post(
        "http://localhost:8080",
        json={"transaction": str},
        timeout=30,
    )
    print(response)


def test12():
    tx = (
        TopicMessageSubmitTransaction().set_topic_id(TopicId.from_string("0.0.10765413")).set_message("hello world")
    ).freeze_with(client)
    tx.sign(submitKey)

    str = base64.b64encode(tx.to_bytes()).decode()

    response = requests.post(
        "http://localhost:8080",
        json={"transaction": str},
        timeout=30,
    )
    print(response)


def test13():
    tx = TopicMessageSubmitTransaction().set_topic_id(TopicId.from_string("0.0.10765413")).set_message("hello world")

    str = base64.b64encode(tx.to_bytes()).decode()

    response = requests.post(
        "http://localhost:8080",
        json={"transaction": str, "sign": True},
        timeout=30,
    )
    print(response)


def test14():
    tx = (
        TopicMessageSubmitTransaction().set_topic_id(TopicId.from_string("0.0.10765413")).set_message("a" * 1025)
    ).freeze_with(client)

    str = base64.b64encode(tx.to_bytes()).decode()

    response = requests.post(
        "http://localhost:8080",
        json={"transaction": str, "sign": True},
        timeout=30,
    )
    print(response)


def test15():
    tx = (
        TopicMessageSubmitTransaction()
        .set_topic_id(TopicId.from_string("0.0.10765413"))
        .set_message("a" * 1025)
        .set_node_account_ids(
            [AccountId.from_string("0.0.3"), AccountId.from_string("0.0.4"), AccountId.from_string("0.0.2")]
        )
        .set_transaction_id(TransactionId.generate(client.operator_account_id))
    ).freeze()

    str = base64.b64encode(tx.to_bytes()).decode()

    response = requests.post(
        "http://localhost:8080",
        json={"transaction": str, "sign": True},
        timeout=30,
    )
    print(response)


def test16():
    tx = FileAppendTransaction().set_file_id(FileId.from_string("0.0.10765910")).set_contents("test python")
    str = base64.b64encode(tx.to_bytes()).decode()

    response = requests.post(
        "http://localhost:8080",
        json={"transaction": str},
        timeout=30,
    )
    print(response)


def test17():
    tx = (
        FileAppendTransaction()
        .set_file_id(FileId.from_string("0.0.10765910"))
        .set_contents("test python")
        .freeze_with(client)
    )
    str = base64.b64encode(tx.to_bytes()).decode()

    response = requests.post(
        "http://localhost:8080",
        json={"transaction": str},
        timeout=30,
    )
    print(response)


def test18():
    tx = (
        FileAppendTransaction()
        .set_file_id(FileId.from_string("0.0.10765910"))
        .set_contents("p" * 4098)
        .freeze_with(client)
    )
    str = base64.b64encode(tx.to_bytes()).decode()

    response = requests.post(
        "http://localhost:8080",
        json={"transaction": str},
        timeout=30,
    )
    print(response)


def test19():
    tx = FileAppendTransaction().set_file_id(FileId.from_string("0.0.10765910")).set_contents("o" * 4098)
    str = base64.b64encode(tx.to_bytes()).decode()

    response = requests.post(
        "http://localhost:8080",
        json={"transaction": str},
        timeout=30,
    )
    print(response)

    print(FileContentsQuery().set_file_id(FileId.from_string("0.0.10765910")).execute(client))


def main():
    test1()
    test2()
    test3()
    test4()
    test5()
    test6()
    test7()
    test8()
    test9()
    test10()
    test11()
    test12()
    test13()
    test14()
    test15()
    test16()
    test17()
    test18()
    test19()


if __name__ == "__main__":
    main()
