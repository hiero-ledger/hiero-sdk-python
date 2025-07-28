#!/usr/bin/env python3

"""
File Append Example

This example demonstrates how to append content to an existing file on the network.
It shows both single-chunk and multi-chunk append operations.
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from hiero_sdk_python import (
    Client, Network, PrivateKey, FileCreateTransaction, AccountId,
    FileAppendTransaction, ResponseCode
)

def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network='testnet')
    client = Client(network)

    print(os.getenv('OPERATOR_ID'))
    print(os.getenv('OPERATOR_KEY'))

    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
    client.set_operator(operator_id, operator_key)
    
    
    return client

def file_append():
    """
    Demonstrates appending content to a file on the network by:
    1. Setting up client with operator account
    2. Creating a file with initial content
    3. Appending additional content to the file
    """
    client = setup_client()
    
    file_private_key = PrivateKey.generate_ed25519()
    
    # Step 1: Create a file with initial content
    print("Creating file with initial content...")
    create_receipt = (
        FileCreateTransaction()
        .set_keys(file_private_key.public_key())
        .set_contents(b"Initial file content")
        .set_file_memo("File for append example")
        .freeze_with(client)
        .sign(file_private_key)
        .execute(client)
    )
    
    if create_receipt.status != ResponseCode.SUCCESS:
        print(f"File creation failed with status: {ResponseCode(create_receipt.status).name}")
        sys.exit(1)
    
    file_id = create_receipt.file_id
    print(f"File created successfully with ID: {file_id}")
    
    # Step 2: Append content to the file (single chunk)
    print("\nAppending content to file (single chunk)...")
    append_receipt = (
        FileAppendTransaction()
        .set_file_id(file_id)
        .set_contents(b"\nThis is appended content!")
        .freeze_with(client)
        .sign(file_private_key)
        .execute(client)
    )
    
    if append_receipt.status != ResponseCode.SUCCESS:
        print(f"File append failed with status: {ResponseCode(append_receipt.status).name}")
        sys.exit(1)
    
    print("Content appended successfully!")
    
    # Step 3: Append large content (multi-chunk)
    print("\nAppending large content (multi-chunk)...")
    large_content = b"Large content that will be split into multiple chunks. " * 100
    
    large_append_receipt = (
        FileAppendTransaction()
        .set_file_id(file_id)
        .set_contents(large_content)
        .set_chunk_size(1024)  # 1KB chunks
        .set_max_chunks(50)    # Allow up to 50 chunks
        .freeze_with(client)
        .sign(file_private_key)
        .execute(client)
    )
    
    if large_append_receipt.status != ResponseCode.SUCCESS:
        print(f"Large file append failed with status: {ResponseCode(large_append_receipt.status).name}")
        sys.exit(1)
    
    print("Large content appended successfully!")
    print(f"Total chunks used: {FileAppendTransaction().set_contents(large_content).get_required_chunks()}")

if __name__ == "__main__":
    file_append() 