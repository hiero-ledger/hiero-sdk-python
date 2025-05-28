"""
Integration test for TokenUnpauseTransaction.

Tests the actual execution of a token unpause transaction against a test network.
"""
import os
import unittest

from hiero_sdk_python import Client
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_unpause_transaction import TokenUnpauseTransaction

class TestTokenUnpauseTransactionE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize client with testnet credentials
        cls.client = Client.for_testnet()
        operator_id = os.getenv('OPERATOR_ID')
        operator_key = os.getenv('OPERATOR_KEY')
        
        if not operator_id or not operator_key:
            raise unittest.SkipTest("OPERATOR_ID and OPERATOR_KEY environment variables must be set for integration tests")
            
        cls.client.set_operator(operator_id, operator_key)
        
        # Create or get a test token with pause key
        # This would typically be set up in a test fixture
        cls.test_token_id = TokenId.from_string(os.getenv('TEST_TOKEN_ID_WITH_PAUSE_KEY'))
        if not cls.test_token_id:
            raise unittest.SkipTest("TEST_TOKEN_ID_WITH_PAUSE_KEY environment variable must be set for this test")

    def test_token_unpause_transaction_can_execute(self):
        """Test that a token unpause transaction can be executed successfully."""
        # Create and execute the unpause transaction
        transaction = TokenUnpauseTransaction()\
            .set_token_id(self.test_token_id)
        
        # Execute the transaction
        response = transaction.execute(self.client)
        
        # Verify the transaction was successful
        receipt = response.getReceipt(self.client)
        self.assertEqual(receipt.status, "SUCCESS")
        
        # Additional verification could be added here to check the token's pause status
        # This would typically require querying the token info

if __name__ == '__main__':
    unittest.main()
