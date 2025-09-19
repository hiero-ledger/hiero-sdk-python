import os
import sys
from dotenv import load_dotenv
from hiero_sdk_python import (
 Client,
 Network,
 AccountId,
 PrivateKey,
 Hbar,
 AccountCreateTransaction,
 TokenCreateTransaction,
 TokenAirdropTransaction,
 TokenAssociateTransaction,
 TokenMintTransaction,
 CryptoGetAccountBalanceQuery,
 TokenType,
 ResponseCode,
 NftId,
 TransactionRecordQuery
)
 # Check the transaction record to verify the contents

load_dotenv()

def setup_client():
    """Initialize and set up the client with operator account"""
    print("Connecting to Hedera testnet...")
    client = Client(Network(network='testnet'))

    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
        operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
        client.set_operator(operator_id, operator_key)

        return client, operator_id, operator_key
    except (TypeError, ValueError):
        print("❌ Error: Creating client, Please check your .env file")
        sys.exit(1)

def create_account(client, operator_key):
    """Create a new recipient account"""
    print("\nCreating a new account...")
    recipient_key = PrivateKey.generate()

    try:
        account_tx = (
            AccountCreateTransaction()
            .set_key(recipient_key.public_key())
            .set_initial_balance(Hbar.from_tinybars(100_000_000))
        )
        account_receipt = account_tx.freeze_with(client).sign(operator_key).execute(client)
        recipient_id = account_receipt.account_id
        print(f"✅ Success! Created a new recipient account with ID: {recipient_id}")

        return recipient_key, recipient_id
    except Exception as e:
        print(f"❌ Error creating new recipient account: {e}")
        sys.exit(1)

def create_token(client, operator_id, operator_key):
    """Create a fungible token"""
    print("\nStep 1: Creating a fungible token (TKA)...")
    try:
        token_tx = (
            TokenCreateTransaction()
            .set_token_name("Token A")
            .set_token_symbol("TKA")
            .set_initial_supply(1)
            .set_token_type(TokenType.FUNGIBLE_COMMON)
            .set_treasury_account_id(operator_id)
        )
        token_receipt = token_tx.freeze_with(client).sign(operator_key).execute(client)
        token_id = token_receipt.token_id

        print(f"✅ Success! Created token: {token_id}")

        return token_id
    except Exception as e:
        print(f"❌ Error creating token: {e}")
        sys.exit(1)

def create_nft(client, operator_key, operator_id):
    """Create a NFT"""
    print("\nStep 2: Creating a non-fungible token (NFTA)...")
    try:
        nft_tx = (
            TokenCreateTransaction()
            .set_token_name("Token B")
            .set_token_symbol("NFTA")
            .set_initial_supply(0)
            .set_supply_key(operator_key)
            .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
            .set_treasury_account_id(operator_id)
        )
        nft_receipt = nft_tx.freeze_with(client).sign(operator_key).execute(client)
        nft_id = nft_receipt.token_id

        print(f"✅ Success! Created nft: {nft_id}")
        return nft_id
    except Exception as e:
        print(f"❌ Error creating nft: {e}")
        sys.exit(1)

def mint_nft(client, operator_key, nft_id):
    """Mint the NFT with metadata"""
    print("\nStep 3: Minting an NFT for NFTA...")
    try:
        mint_tx = TokenMintTransaction(token_id=nft_id, metadata=[b"NFT data"])
        mint_tx.freeze_with(client)
        mint_tx.sign(operator_key)
        mint_receipt = mint_tx.execute(client)

        serial_number = mint_receipt.serial_numbers[0]
        print(f"✅ Success! Nft minted serial: { serial_number }.")
        return serial_number
    except Exception as e:
        print(f"❌ Error minting nft: {e}")
        sys.exit(1)

def associate_tokens(client, recipient_id, recipient_key, tokens):
    """Associate the token and nft with the recipient"""
    print("\nStep 4: Associating tokens to recipient...")
    try:
        associate_tx = TokenAssociateTransaction(
            account_id=recipient_id,
            token_ids=tokens
        )
        associate_tx.freeze_with(client)
        associate_tx.sign(recipient_key)
        associate_receipt = associate_tx.execute(client)

        # Verify association was successful
        if associate_receipt.status != ResponseCode.SUCCESS:
            print(f"❌ Failed to associate tokens: Status: {associate_receipt.status}")
            sys.exit(1)

        balance_before = (
            CryptoGetAccountBalanceQuery(account_id=recipient_id)
            .execute(client)
            .token_balances
        )
        print("Tokens associated with recipient (should be 0 for both):")
        print(f"  {tokens[0]}: {balance_before.get(tokens[0], 0)}")
        print(f"  {tokens[1]}: {balance_before.get(tokens[1], 0)}")
        print("\n✅ Success! Token association complete.")

    except Exception as e:
        print(f"❌ Error associating tokens: {e}")
        sys.exit(1)


def token_airdrop():
    """
    A full example that creates an account, a token, associate token, and 
    finally perform token airdrop.
    """
    # Setup Client
    client, operator_id, operator_key = setup_client()

    # Create a new account
    recipient_key, recipient_id = create_account(client, operator_key)

    # Create a tokens
    token_id = create_token(client, operator_id, operator_key)

    # Create a nft
    nft_id = create_nft(client, operator_key, operator_id)

    # Mint nft
    serial_number = mint_nft(client, operator_key, nft_id)
    print(f"Using NFT with serial #{serial_number} for the airdrop")

    # Associate tokens
    associate_tokens(client, recipient_id, recipient_key, [token_id, nft_id])

    # Log balances before airdrop
    print("\nStep 5: Checking balances before airdrop...")
    sender_balances_before = CryptoGetAccountBalanceQuery(account_id=operator_id).execute(client).token_balances
    recipient_balances_before = CryptoGetAccountBalanceQuery(account_id=recipient_id).execute(client).token_balances
    print(f"Sender ({operator_id}) balances before airdrop:")
    print(f"  {token_id}: {sender_balances_before.get(token_id, 0)}")
    print(f"  {nft_id}: {sender_balances_before.get(nft_id, 0)}")
    print(f"Recipient ({recipient_id}) balances before airdrop:")
    print(f"  {token_id}: {recipient_balances_before.get(token_id, 0)}")
    print(f"  {nft_id}: {recipient_balances_before.get(nft_id, 0)}")

    # Airdrop the tokens
    print(f"\nStep 6: Airdropping tokens to recipient {recipient_id}:")
    print(f"  - 1 fungible token TKA ({token_id})")
    print(f"  - NFT from NFTA collection ({nft_id}) with serial number #{serial_number}")
    try:
        airdrop_receipt = (
            TokenAirdropTransaction()
            .add_token_transfer(token_id=token_id, account_id=operator_id, amount=-1)
            .add_token_transfer(token_id=token_id, account_id=recipient_id, amount=1)
            .add_nft_transfer(
                nft_id=NftId(token_id=nft_id, serial_number=serial_number),
                sender=operator_id, receiver=recipient_id
            )
            .freeze_with(client)
            .sign(operator_key)
            .execute(client)
        )

        if airdrop_receipt.status != ResponseCode.SUCCESS:
            print(f"❌ Fail to airdrop: Status: {airdrop_receipt.status}")
            sys.exit(1)

        print(f"Token airdrop ID: {airdrop_receipt.transaction_id}")
        print("\nVerifying airdrop contents:")
        print(f"  - Transaction status: {airdrop_receipt.status}")
        
        record = TransactionRecordQuery(transaction_id=airdrop_receipt.transaction_id).execute(client)
        
        # Check token transfers
        print("  - Token transfers in this transaction:")
        expected_token_transfer = False
        for token_id_key, transfers in record.token_transfers.items():
            is_expected_token = token_id_key == token_id
            token_indicator = "✓ EXPECTED" if is_expected_token else ""
            print(f"    Token {token_id_key}: {token_indicator}")
            
            # Check for the expected transfer pattern
            sender_sent_one = False
            recipient_received_one = False
            
            for account, amount in transfers.items():
                if amount > 0:
                    print(f"      → {account} received {amount} token(s)")
                    if account == recipient_id and amount == 1 and is_expected_token:
                        recipient_received_one = True
                else:
                    print(f"      → {account} sent {abs(amount)} token(s)")
                    if account == operator_id and amount == -1 and is_expected_token:
                        sender_sent_one = True
                        
            if sender_sent_one and recipient_received_one:
                expected_token_transfer = True
            
        # Verify the expected fungible token transfer
        print("\nVerifying expected fungible token transfer:")
        if expected_token_transfer:
            print(f"  ✅ Success! 1 token of {token_id} (TKA) was successfully transferred")
            print(f"      from {operator_id} to {recipient_id}")
        else:
            print(f"  ⚠️ Warning: Could not confirm transfer of 1 token of {token_id} (TKA)")
            print(f"      This might indicate an issue with the transaction or record retrieval")
        
        # Instead of trying to parse the NFT transfers from the record (which has a complex structure),
        # we'll verify the NFT transfer through balance changes, which is more reliable
        print("  - Verifying NFT transfer through balance changes:")
        expected_serial_transferred = False
        
        # Check if balances reflect the NFT transfer
        try:
            # Get updated balances right now to verify transfer
            sender_current = CryptoGetAccountBalanceQuery(account_id=operator_id).execute(client).token_balances
            recipient_current = CryptoGetAccountBalanceQuery(account_id=recipient_id).execute(client).token_balances
            
            # Check if the NFT balance changed as expected
            sender_nft_before = sender_balances_before.get(nft_id, 0)
            sender_nft_after = sender_current.get(nft_id, 0)
            recipient_nft_before = recipient_balances_before.get(nft_id, 0)
            recipient_nft_after = recipient_current.get(nft_id, 0)
            
            print(f"    Sender NFT balance: {sender_nft_before} -> {sender_nft_after}")
            print(f"    Recipient NFT balance: {recipient_nft_before} -> {recipient_nft_after}")
            
            # If the sender's balance decreased by 1 and the recipient's increased by 1, 
            # we can infer that the NFT was transferred
            if sender_nft_before > sender_nft_after and recipient_nft_after > recipient_nft_before:
                expected_serial_transferred = True
                print(f"    ✓ EXPECTED: Balance changes confirm NFT transfer")
                print(f"      → NFT with serial #{serial_number} was transferred from {operator_id} to {recipient_id}")
            
        except Exception as e:
            print(f"    Error verifying NFT transfer through balances: {str(e)}")
        
        # Store the updated balances for later use
        sender_balances_after = sender_current
        recipient_balances_after = recipient_current
        
        # Verify the specific serial we intended to transfer
        print("\nVerifying expected NFT transfer:")
        if expected_serial_transferred:
            print(f"  ✅ Success! NFT {nft_id} with serial #{serial_number} was successfully transferred")
            print(f"      from {operator_id} to {recipient_id}")
        else:
            print(f"  ⚠️ Warning: Could not confirm transfer of NFT {nft_id} with serial #{serial_number}")
            print(f"      This might indicate an issue with the transaction or record retrieval")
        
        # Log balances after airdrop
        sender_balances_after = CryptoGetAccountBalanceQuery(account_id=operator_id).execute(client).token_balances
        recipient_balances_after = CryptoGetAccountBalanceQuery(account_id=recipient_id).execute(client).token_balances
        print("\nBalances after airdrop:")
        print(f"Sender ({operator_id}):")
        print(f"  {token_id}: {sender_balances_after.get(token_id, 0)}")
        print(f"  {nft_id}: {sender_balances_after.get(nft_id, 0)}")
        print(f"Recipient ({recipient_id}):")
        print(f"  {token_id}: {recipient_balances_after.get(token_id, 0)}")
        print(f"  {nft_id}: {recipient_balances_after.get(nft_id, 0)}")

        # Summary table
        print("\nSummary Table:")
        print("+----------------+----------------------+----------------------+----------------------+----------------------+")
        print("| Token Type     | Token ID             | NFT Serial          | Sender Balance       | Recipient Balance    |")
        print("+----------------+----------------------+----------------------+----------------------+----------------------+")
        print(f"| Fungible (TKA) | {str(token_id):20} | {'N/A':20} | {str(sender_balances_after.get(token_id, 0)):20} | {str(recipient_balances_after.get(token_id, 0)):20} |")
        print(f"| NFT (NFTA)     | {str(nft_id):20} | #{str(serial_number):19} | {str(sender_balances_after.get(nft_id, 0)):20} | {str(recipient_balances_after.get(nft_id, 0)):20} |")
        print("+----------------+----------------------+----------------------+----------------------+----------------------+")
        print("\n✅ Success! Token Airdrop transaction successful")
    except Exception as e:
        print(f"❌ Error airdropping tokens: {e}")
        sys.exit(1)

if __name__ == "__main__":
    token_airdrop()

