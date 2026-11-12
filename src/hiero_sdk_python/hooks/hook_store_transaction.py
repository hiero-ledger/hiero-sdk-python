"""HookStoreTransaction class for HIP-1195 hooks."""

from __future__ import annotations

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services import transaction_pb2
from hiero_sdk_python.hapi.services.hook_store_pb2 import HookStoreTransactionBody
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hooks.evm_hook_storage_update import EvmHookStorageUpdate
from hiero_sdk_python.hooks.hook_id import HookId
from hiero_sdk_python.transaction.transaction import Transaction


class HookStoreTransaction(Transaction):
    """
    Adds, changes or removes key/value pairs in the storage of an EVM hook.

    The transaction must be signed by the hook's admin key, or by the key of the
    account or contract that owns the hook if it has no admin key.

    Example:
        ```python
        hook_id = HookId(HookEntityId(account_id=owner_id), 1)
        receipt = (
            HookStoreTransaction()
            .set_hook_id(hook_id)
            .add_storage_update(EvmHookStorageSlot(key=b"\\x01", value=b"\\x02"))
            .freeze_with(client)
            .sign(owner_key)
            .execute(client)
        )
        ```
    """

    def __init__(
        self,
        hook_id: HookId | None = None,
        storage_updates: list[EvmHookStorageUpdate] | None = None,
    ) -> None:
        """
        Initializes a new HookStoreTransaction.

        Args:
            hook_id (HookId, optional): The hook whose storage is updated.
            storage_updates (list[EvmHookStorageUpdate], optional): The storage changes.
        """
        super().__init__()
        self.hook_id: HookId | None = None
        self.storage_updates: list[EvmHookStorageUpdate] = []

        if hook_id is not None:
            self.set_hook_id(hook_id)
        if storage_updates is not None:
            self.set_storage_updates(storage_updates)

    def set_hook_id(self, hook_id: HookId) -> HookStoreTransaction:
        """
        Sets the hook whose storage is updated.

        Args:
            hook_id (HookId): The fully qualified hook ID.

        Returns:
            HookStoreTransaction: This transaction instance.

        Raises:
            TypeError: If hook_id is not a HookId.
        """
        self._require_not_frozen()
        if not isinstance(hook_id, HookId):
            raise TypeError("hook_id must be a HookId instance.")
        self.hook_id = hook_id
        return self

    def set_storage_updates(self, storage_updates: list[EvmHookStorageUpdate]) -> HookStoreTransaction:
        """
        Replaces the list of storage updates.

        Args:
            storage_updates (list[EvmHookStorageUpdate]): The storage changes.

        Returns:
            HookStoreTransaction: This transaction instance.

        Raises:
            TypeError: If storage_updates is not a list of EvmHookStorageUpdate.
        """
        self._require_not_frozen()
        if not isinstance(storage_updates, list | tuple) or not all(
            isinstance(update, EvmHookStorageUpdate) for update in storage_updates
        ):
            raise TypeError("storage_updates must be a list of EvmHookStorageUpdate.")
        self.storage_updates = list(storage_updates)
        return self

    def add_storage_update(self, storage_update: EvmHookStorageUpdate) -> HookStoreTransaction:
        """
        Appends a storage update.

        Args:
            storage_update (EvmHookStorageUpdate): The storage change to add.

        Returns:
            HookStoreTransaction: This transaction instance.

        Raises:
            TypeError: If storage_update is not an EvmHookStorageUpdate.
        """
        self._require_not_frozen()
        if not isinstance(storage_update, EvmHookStorageUpdate):
            raise TypeError("storage_update must be an EvmHookStorageUpdate instance.")
        self.storage_updates.append(storage_update)
        return self

    def _build_proto_body(self) -> HookStoreTransactionBody:
        """
        Builds the protobuf body for the hook store transaction.

        Returns:
            HookStoreTransactionBody: The protobuf body.

        Raises:
            ValueError: If hook_id is not set.
        """
        if self.hook_id is None:
            raise ValueError("Missing required HookId")
        return HookStoreTransactionBody(
            hook_id=self.hook_id._to_proto(),
            storage_updates=[update._to_proto() for update in self.storage_updates],
        )

    def build_transaction_body(self) -> transaction_pb2.TransactionBody:
        """
        Builds the transaction body for the hook store transaction.

        Returns:
            TransactionBody: The protobuf transaction body.
        """
        hook_store_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.hook_store.CopyFrom(hook_store_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        HookStoreTransaction cannot be scheduled.

        Raises:
            ValueError: Always.
        """
        raise ValueError("Cannot schedule a HookStoreTransaction")

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Returns the gRPC method for submitting a hook store transaction.

        Args:
            channel (_Channel): The channel containing the service stubs.

        Returns:
            _Method: The method wrapper for SmartContractService.hookStore.
        """
        return _Method(transaction_func=channel.smart_contract.hookStore, query_func=None)

    @classmethod
    def _from_protobuf(cls, transaction_body: transaction_pb2.TransactionBody) -> HookStoreTransaction:
        """
        Creates a HookStoreTransaction from a protobuf TransactionBody.

        Args:
            transaction_body (TransactionBody): The parsed transaction body.

        Returns:
            HookStoreTransaction: A new instance with the hook ID and storage updates restored.
        """
        transaction = super()._from_protobuf(transaction_body)

        if transaction_body.HasField("hook_store"):
            body = transaction_body.hook_store
            if body.HasField("hook_id"):
                transaction.hook_id = HookId._from_proto(body.hook_id)
            transaction.storage_updates = [EvmHookStorageUpdate._from_proto(update) for update in body.storage_updates]

        return transaction
