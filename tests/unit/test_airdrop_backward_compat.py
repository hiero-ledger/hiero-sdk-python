import unittest
import warnings

# We test the old import path, which should now exist because of the compatibility file
OLD_IMPORT_PATH = 'hiero_sdk_python.tokens.token_cancel_airdrop_transaction'

class TestAirdropCompatibility(unittest.TestCase):

    def test_deprecated_import_succeeds_and_warns(self):
        """
        Tests that importing the class via the old file name succeeds and emits
        the expected DeprecationWarning.
        """

        # The expected warning message content (or part of it)
        expected_message_part = "TokenCancelAirdropTransaction has been moved"

        # 1. Check that the DeprecationWarning is raised
        with self.assertRaises(DeprecationWarning) as cm:
            # 2. Attempt the old import
            __import__(OLD_IMPORT_PATH)

        # 3. Assert the warning message is correct
        self.assertIn(expected_message_part, str(cm.exception))

        # 4. Check the imported object exists and is the correct type (optional but good)
        # This requires safely importing the class *again* without raising the exception
        import sys
        old_module = sys.modules[OLD_IMPORT_PATH]

        # Assert the class exists inside the old module
        self.assertTrue(hasattr(old_module, 'TokenCancelAirdropTransaction'))

# If running directly (optional)
if __name__ == '__main__':
    unittest.main()