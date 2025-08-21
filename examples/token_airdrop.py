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
 NftId
)

load_dotenv()

def token_airdrop():
    """
    A full example that creates an account, a token, associate token, and 
    finally perform token airdrop.
    """

    # Setup Client
    print("Connecting to Hedera testnet...")
    client = Client(Network(network='testnet'))

    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
        operator_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))
        client.set_operator(operator_id, operator_key)
    except (TypeError, ValueError):
        print("❌ Error: Creating client, Please check your .env file")
        sys.exit(1)

    # Create a new account
    print("\nCreating a new account...")
    recipient_key = PrivateKey.generate_ecdsa()
    
    try:
        account_tx = (
            AccountCreateTransaction()
            .set_key(recipient_key.public_key())
            .set_initial_balance(Hbar.from_tinybars(100_000_000))
        )
        account_receipt = account_tx.freeze_with(client).sign(operator_key).execute(client)
        recipient_id = account_receipt.account_id
        print(f"✅ Success! Created a new account with ID: {recipient_id}")
    except Exception as e:
        print(f"❌ Error creating new account: {e}")
        sys.exit(1)

    # Create a tokens
    print("\nCreating a token...")
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
    except Exception as e:
        print(f"❌ Error creating token: {e}")
        sys.exit(1)

    # Create a nft
    print("\nCreating a nft...")
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
    except Exception as e:
        print(f"❌ Error creating nft: {e}")
        sys.exit(1)

    #Mint nft
    print("Minting a nft...")
    try:
        mint_tx = TokenMintTransaction(token_id=nft_id, metadata=[b"NFT data"])
        mint_tx.freeze_with(client)
        mint_tx.sign(operator_key)
        mint_receipt = mint_tx.execute(client)

        serial_number = mint_receipt.serial_numbers[0]
        print(f"✅ Success! Nft minted serial: { serial_number }.")
    except Exception as e:
        print(f"❌ Error minting nft: {e}")

    # Associate tokens
    print("\nAssociating tokens to recipient...")
    try:
        assocciate_tx = TokenAssociateTransaction(
            account_id=recipient_id, 
            token_ids=[token_id, nft_id]
        )
        assocciate_tx.freeze_with(client)
        assocciate_tx.sign(recipient_key)
        assocciate_tx.execute(client)
        print(f"✅ Success! Token association complete.")

    except Exception as e:
        print(f"❌ Error associating tokens: {e}")

    # Airdrop Tthe tokens
    print("\nAirdropping tokens...")
    try:
        airdrop_receipt = (
            TokenAirdropTransaction()
            .add_token_transfer(token_id=token_id, account_id=operator_id, amount=-1)
            .add_token_transfer(token_id=token_id, account_id=recipient_id, amount=1)
            .add_nft_transfer(nft_id=NftId(token_id=nft_id, serial_number=serial_number), sender=operator_id, receiver=recipient_id)
            .freeze_with(client)
            .sign(operator_key)
            .execute(client)
        )
        if (airdrop_receipt.status != ResponseCode.SUCCESS):
            print(f"Fail to cancel airdrop: Status: {airdrop_receipt.status}")
            sys.exit(1)

        print(f"Token airdrop ID: {airdrop_receipt.transaction_id}")
        
        balance = CryptoGetAccountBalanceQuery(account_id=recipient_id).execute(client)
        print(f"Token balance after airdrop balance:{balance.token_balances}")
        print("\n✅ Success! Token Airdrop transaction successfull")
    except Exception as e:
        print(f"❌ Error airdropping tokens: {e}")
        sys.exit(1)

if __name__ == "__main__":
    token_airdrop()
