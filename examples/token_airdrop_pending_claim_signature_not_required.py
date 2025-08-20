# Similar example but:

# #    tx_create_account = (
#        AccountCreateTransaction()
#        .set_key(receiver_public_key)
#        .set_initial_balance(Hbar(1))
#        .set_receiver_signature_required(False) <-- FALSE
#        .freeze_with(client)
#    )

# Now the airdrop will be automatic with enough auto-association slots
# TO DO: we need to add max auto association functionality to account create

# Once we have that, the airdrop should arrive since the user doesn't need to sign and has auto associate

# We should illustrate what happens if they have run out of auto associate slots, and they'll need to associate their tokens.


# def associate_tokens_once(client, account_id, account_private_key, token_ids):
#     tx = TokenAssociateTransaction().set_account_id(account_id)
#     for tid in token_ids:
#         tx.add_token_id(tid)

#     tx = tx.freeze_with(client).sign(account_private_key)

#     try:
#         receipt = tx.execute(client)
#         status = ResponseCode(receipt.status)
#         if status not in (ResponseCode.SUCCESS,):
#             raise RuntimeError(f"Association failed: {status.name} ({receipt.status})")
#         print(f"✅ Association status: {status.name} ({receipt.status})")
#         return receipt
#     except Exception as e:
#         raise SystemExit(f"failed to associate tokens: {e}") from e

# # Associate all the tokens at once
# all_token_ids = [
#     airdrop_fungible_token_id_1,
#     airdrop_fungible_token_id_2,
#     airdrop_nft_token_id_1,   # note: associate NFT *token id*, not a serial
# ]

# associate_tokens_once(client, receiver_id, receiver_private_key, all_token_ids)

# def verify_associations(client, account_id, token_ids):
#     info = AccountInfoQuery(account_id).execute(client)
#     rels = getattr(info, "token_relationships", [])

#     associated = {str(r.token_id) for r in rels}

#     missing = []
#     for tid in token_ids:
#         ok = 1 if str(tid) in associated else 0
#         print(f"Associated({tid}) = {ok}")
#         if not ok:
#             missing.append(tid)

#     if missing:
#         raise RuntimeError(f"Account {account_id} is missing associations for: {', '.join(map(str, missing))}")

#     print(f"✅ All {len(token_ids)} tokens associated to {account_id}. The receiver is {receiver_id}")
#     return True

# Call to verify the associations for each
# verify_associations(client, receiver_id, all_token_ids)

# # #  associate the receiver to allow claim to finalize balances into their account
# # associate_rx = (
# #     TokenAssociateTransaction()
# #     .set_account_id(receiver_id)
# #     .add_token_id(fungible_token_id_1)
# #     .add_token_id(fungible_token_id_2)
# #     .add_token_id(nft_token_id_1)
# #     .freeze_with(client)
# #     .sign(receiver_private_key)
# # )
# # assoc_receipt = associate_rx.execute(client)
# # print("Receiver associate status:", ResponseCode(assoc_receipt.status).name, assoc_receipt.status)
