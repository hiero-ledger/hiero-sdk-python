from __future__ import annotations

from dataclasses import dataclass

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transaction_id import TransactionId
from tck.util.param_utils import to_bool, to_int


@dataclass
class CommonTransactionParams:
    transactionId: str | None = None
    maxTransactionFee: int | None = None
    validTransactionDuration: int | None = None
    memo: str | None = None
    regenerateTransactionId: bool | None = None
    signers: list[str] | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> CommonTransactionParams:
        return cls(
            transactionId=params.get("transactionId"),
            maxTransactionFee=to_int(params.get("maxTransactionFee")),
            validTransactionDuration=to_int(params.get("validTransactionDuration")),
            memo=params.get("memo"),
            regenerateTransactionId=to_bool(params.get("regenerateTransactionId")),
            signers=[signer for signer in params.get("signers", [])],
        )

    def apply_common_params(self, transaction: Transaction, client: Client) -> None:
        """Apply commonTransactionParams to a given transaction."""
        if self.transactionId is not None:
            try:
                transaction.set_transaction_id(TransactionId.from_string(self.transactionId))
            except Exception:
                transaction.set_transaction_id(TransactionId.generate(AccountId.from_string(self.transactionId)))

        # TODO add a max_transaction_fee sdk missing func

        if self.validTransactionDuration is not None:
            transaction.set_transaction_valid_duration(self.validTransactionDuration)

        if self.memo is not None:
            transaction.set_transaction_memo(self.memo)

        # TODO add regenerate_transaction_id sdk missing func

        if self.signers:
            transaction.freeze_with(client)
            for signer in self.signers:
                transaction.sign(PrivateKey.from_string(signer))
