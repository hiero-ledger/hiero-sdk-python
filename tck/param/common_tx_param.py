from dataclasses import dataclass

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transaction_id import TransactionId


@dataclass
class CommonTransactionParams:
  transactionId: str | None = None
  maxTransactionFee: int | None = None
  validTransactionDuration: int | None = None
  memo: str | None = None
  regenerateTransactionId: bool | None = None
  signers: list[str] | None = None

  @classmethod
  def from_dict(cls, params: dict) -> "CommonTransactionParams":
    max_transaction_fee = params.get("maxTransactionFee")
    valid_transaction_duration = params.get("validTransactionDuration")
    regenerate_transaction_id = params.get("regenerateTransactionId")
    signers_list = params.get("signers")

    return cls(
      transactionId=params.get("transactionId"),
      maxTransactionFee=int(max_transaction_fee) if max_transaction_fee else None,
      validTransactionDuration=int(valid_transaction_duration) if valid_transaction_duration else None,
      memo=params.get("memo"),
      regenerateTransactionId=eval(regenerate_transaction_id) if regenerate_transaction_id else None, 
      signers=[signers for signers in signers_list] if signers_list else None
    )
  
  def apply_common_params(self, transaction: Transaction, client: Client) -> None:
    if self.transactionId:
      try:
        transaction.set_transaction_id(TransactionId.from_string(self.transactionId))
      except:
        transaction.set_transaction_id(TransactionId.generate(AccountId.from_string(self.transactionId)))
    
    # TODO add a max_transaction_fee

    if self.validTransactionDuration:
      transaction.set_transaction_valid_duration(self.validTransactionDuration)

    if self.memo:
      transaction.set_transaction_memo(self.memo)

    # TODO add regenerate_transaction_id

    if self.signers:
      transaction.freeze_with(client)
      for signer in self.signers:
        transaction.sign(PrivateKey.from_string(signer));
