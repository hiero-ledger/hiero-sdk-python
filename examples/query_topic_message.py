import os
import time
from datetime import datetime
from dotenv import load_dotenv

from hiero_sdk_python import Network, Client, TopicMessageQuery

load_dotenv()

def query_topic_messages():
    network = Network(network='testnet')
    client = Client(network)

    def on_message_handler(topic_message):
        print(f"Received topic message: {topic_message}")

    def on_error_handler(e):
        print(f"Subscription error: {e}")

    query = TopicMessageQuery(
        topic_id=os.getenv('TOPIC_ID'),
        start_time=datetime.utcnow(),
        limit=0,
        chunking_enabled=True
    )

    handle = query.subscribe(
        client,
        on_message=on_message_handler,
        on_error=on_error_handler
    )

    print("Subscription started. Press Ctrl+C to cancel...")
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("Cancelling subscription...")
        handle.cancel() 
        handle.join()    
        print("Subscription cancelled. Exiting.")

if __name__ == "__main__":
    query_topic_messages()
