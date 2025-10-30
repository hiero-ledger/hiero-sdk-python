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
network_name = os.getenv('NETWORK', 'testnet').lower()

def setup_client():
    """Initialize and set up the client with operator account"""
    print(f"🌐 Connecting to Hedera {network_name}...")
    client = Client(Network(network_name))


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

        return token_id
    except Exception as e:
        print(f"❌ Error creating token: {e}")
        sys.exit(1)

def create_nft(client, operator_key, operator_id):
    """Create a NFT"""
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
        return nft_id
    except Exception as e:
        print(f"❌ Error creating nft: {e}")
        sys.exit(1)

def mint_nft(client, operator_key, nft_id):
    """Mint the NFT with metadata"""
    print("\nMinting a nft...")
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
    print("\nAssociating tokens to recipient...")
    try:
        assocciate_tx = TokenAssociateTransaction(
            account_id=recipient_id,
            token_ids=tokens
        )
        assocciate_tx.freeze_with(client)
        assocciate_tx.sign(recipient_key)
        assocciate_tx.execute(client)

        balance_before = (
            CryptoGetAccountBalanceQuery(account_id=recipient_id)
            .execute(client)
            .token_balances
        )
        print("Tokens associated with recipient:")
        print(f"{tokens[0]}: {balance_before.get(tokens[0])}")
        print(f"{tokens[1]}: {balance_before.get(tokens[1])}")

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

    #Mint nft
    serial_number = mint_nft(client, operator_key, nft_id)

    # Associate tokens
    associate_tokens(client, recipient_id, recipient_key, [token_id, nft_id])

    # Airdrop Tthe tokens
    print("\nAirdropping tokens...")
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
            print(f"Fail to cancel airdrop: Status: {airdrop_receipt.status}")
            sys.exit(1)

        print(f"Token airdrop ID: {airdrop_receipt.transaction_id}")

        after_balance = (
            CryptoGetAccountBalanceQuery(account_id=recipient_id)
            .execute(client)
            .token_balances
        )
        print("Recipient balance after token airdrop:")
        print(f"{token_id}: {after_balance.get(token_id)}")
        print(f"{nft_id}: {after_balance.get(nft_id)}")

        print("\n✅ Success! Token Airdrop transaction successful")
    except Exception as e:
        print(f"❌ Error airdropping tokens: {e}")
        sys.exit(1)

if __name__ == "__main__":
    token_airdrop()
