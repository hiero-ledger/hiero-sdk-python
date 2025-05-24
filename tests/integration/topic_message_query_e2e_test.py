import asyncio
import time
from threading import Timer

import pytest

from hiero_sdk_python import ResponseCode, Timestamp, TopicCreateTransaction, TopicDeleteTransaction, TopicMessageQuery, \
    TopicMessageSubmitTransaction
from hiero_sdk_python.consensus.topic_message import TopicMessage
from tests.integration.utils_for_test import IntegrationTestEnv


MESSAGE_WAITING_TIMEOUT = float(10)
waiting_timer: Timer | None = None
last_message_arrival_time = time.time()

async def query_topic_messages(client, topic_id):
    try:
        received_timestamps = []
        messages = []

        completion_future = asyncio.get_running_loop().create_future()

        def complete():
            completion_future.get_loop().call_soon_threadsafe(completion_future.set_result, messages)

            if waiting_timer:
                waiting_timer.cancel()

        def wait_or_complete():
            global waiting_timer
            global last_message_arrival_time

            time_diff = time.time() - last_message_arrival_time

            print(time_diff, time.time(), last_message_arrival_time)

            if time_diff <= MESSAGE_WAITING_TIMEOUT:
                if waiting_timer:
                    waiting_timer.cancel()
                timer_interval = MESSAGE_WAITING_TIMEOUT - time_diff
                waiting_timer = Timer(timer_interval, wait_or_complete)
                waiting_timer.start()
                return
            else:
                complete()

        def on_message(topic_message: TopicMessage):
            print(f"Received Topic Message: {topic_message}")

            global last_message_arrival_time
            last_message_arrival_time = time.time()

            if topic_message.consensus_timestamp in received_timestamps:
                return

            messages.append(topic_message)
            received_timestamps.append(topic_message.consensus_timestamp)

        def handle_error(error: Exception):
            if not completion_future.done() and str(error) != "CANCELLED: unsubscribe":
                completion_future.set_exception(error)

        query = TopicMessageQuery(topic_id=topic_id, start_time=Timestamp(0, 0).to_date())
        query.subscribe(client, on_message, handle_error)

        global last_message_arrival_time
        last_message_arrival_time = time.time()

        wait_or_complete()

        await completion_future

        print(f"Topic Messages: {messages}")

        return completion_future.result()
    except Exception as e:
        print(f"Failed to retrieve topic messages: {str(e)}")


def submit_message(client, topic_id, message):
    transaction = TopicMessageSubmitTransaction(
        topic_id=topic_id,
        message=message
    )
    transaction.freeze_with(client)
    transaction.sign(client.operator_private_key)

    receipt = transaction.execute(client)
    assert receipt.status == ResponseCode.SUCCESS, f"Message submission failed with status: {ResponseCode.get_name(receipt.status)}"


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_integration_topic_message_query_returns_all_messages():
    env = IntegrationTestEnv()

    try:
        create_transaction = TopicCreateTransaction(
            memo="Python SDK topic",
            admin_key=env.public_operator_key
        )

        create_transaction.freeze_with(env.client)
        create_receipt = create_transaction.execute(env.client)
        topic_id = create_receipt.topicId

        submit_message(env.client, topic_id, "First topic message")
        submit_message(env.client, topic_id, "Second topic message")
        submit_message(env.client, topic_id, "Third topic message")

        # Wait until changes are propagated to Hedera Mirror Node
        await asyncio.sleep(10)

        topic_messages = await query_topic_messages(env.client, topic_id)
        assert len(topic_messages) == 3

        delete_transaction = TopicDeleteTransaction(topic_id=topic_id)
        delete_transaction.freeze_with(env.client)
        delete_receipt = delete_transaction.execute(env.client)

        assert delete_receipt.status == ResponseCode.SUCCESS, f"Topic deletion failed with status: {ResponseCode.get_name(delete_receipt.status)}"
    finally:
        env.close()