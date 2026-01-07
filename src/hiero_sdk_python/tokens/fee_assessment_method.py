from enum import Enum

class FeeAssessmentMethod(Enum):
    """
    Fee assessment method for custom token fees:

      • INCLUSIVE – Fee is deducted from the transferred amount.
                     The recipient receives the transferred amount minus the fee.
      
      • EXCLUSIVE – Fee is charged in addition to the transferred amount.
                     The recipient receives the full transferred amount, and the payer
                     pays the fee on top of that.

    This determines whether custom fees are taken from the transaction amount
    or charged separately.
    """

    INCLUSIVE = 0
    EXCLUSIVE = 1
