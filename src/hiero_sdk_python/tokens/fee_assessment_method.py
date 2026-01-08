from enum import Enum

class FeeAssessmentMethod(Enum):
    """Fee assessment method for custom token fees.

    Determines whether custom fees are deducted from the transferred amount
    or charged separately.

    Attributes:
        INCLUSIVE: Fee is deducted from transferred amount.
                    The recipient receives the transferred amount minus the fee.
        EXCLUSIVE: Fee is charged in addition to the transferred amount.
                    The recipient receives the full transferred amount, and the payer
                    pays the fee on top of that.

    Example:
        >>> # Using inclusive fee assessment
        >>> assessment = FeeAssessmentMethod.INCLUSIVE
        >>> print(f"Fee type: {assessment}")
        Fee type: FeeAssessmentMethod.INCLUSIVE

    Args:
        value (int): The numeric value representing the fee assessment method.

    Returns:
        FeeAssessmentMethod: The enum instance for the specified method.
    """

    INCLUSIVE = 0
    EXCLUSIVE = 1
