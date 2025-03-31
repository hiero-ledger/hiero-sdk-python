from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import consensus_create_topic_pb2

class TopicCreateTransaction(Transaction):
    def __init__(self, memo=None, admin_key=None, submit_key=None, auto_renew_period: Duration=None, auto_renew_account=None):
        super().__init__()
        self.memo = memo or ""
        self.admin_key = admin_key
        self.submit_key = submit_key
        self.auto_renew_period: Duration = auto_renew_period or Duration(7890000)
        self.auto_renew_account = auto_renew_account
        self.transaction_fee = 10_000_000

    def set_memo(self, memo):
        self._require_not_frozen()
        self.memo = memo
        return self

    def set_admin_key(self, key):
        self._require_not_frozen()
        self.admin_key = key
        return self

    def set_submit_key(self, key):
        self._require_not_frozen()
        self.submit_key = key
        return self

    def set_auto_renew_period(self, seconds: Duration | int):
        self._require_not_frozen()
        if isinstance(seconds, int):
            self.auto_renew_period = Duration(seconds)
        elif isinstance(seconds, Duration):
            self.auto_renew_period = seconds
        else:
            raise TypeError("Duration of invalid type")
        return self

    def set_auto_renew_account(self, account_id):
        self._require_not_frozen()
        self.auto_renew_account = account_id
        return self

    def build_transaction_body(self):
        """
        Builds and returns the protobuf transaction body for topic creation.

        Returns:
            TransactionBody: The protobuf transaction body containing the topic creation details.

        Raises:
            ValueError: If required fields are missing.
        """
        transaction_body = self.build_base_transaction_body()
        transaction_body.consensusCreateTopic.CopyFrom(consensus_create_topic_pb2.ConsensusCreateTopicTransactionBody(
            adminKey=self.admin_key.to_proto() if self.admin_key is not None else None,
            submitKey=self.submit_key.to_proto() if self.submit_key is not None else None,
            autoRenewPeriod=self.auto_renew_period.to_proto() if self.auto_renew_period is not None else None,
            autoRenewAccount=self.auto_renew_account.to_proto() if self.auto_renew_account is not None else None,
            memo=self.memo
        ))

        return transaction_body

    def _execute_transaction(self, client, transaction_proto):
        """
        Executes the topic creation transaction using the provided client.

        Args:
            client (Client): The client instance to use for execution.
            transaction_proto (Transaction): The protobuf Transaction message.

        Returns:
            TransactionReceipt: The receipt from the network after transaction execution.

        Raises:
            Exception: If the transaction submission fails or receives an error response.
        """
        response = client.topic_stub.createTopic(transaction_proto)

        if response.nodeTransactionPrecheckCode != ResponseCode.OK:
            error_code = response.nodeTransactionPrecheckCode
            error_message = ResponseCode.get_name(error_code)
            raise Exception(f"Error during transaction submission: {error_code} ({error_message})")

        receipt = self.get_receipt(client)
        return receipt
