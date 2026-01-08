from enum import Enum

class FeeAssessmentMethod(Enum):
    """
    Fee assessment method for custom token fees.
    
    Determines whether custom fees are deducted from the transferred amount
    or charged separately from the payer's account.
    
    Attributes:
        INCLUSIVE: Fee is deducted from the transferred amount.
            The recipient receives the transferred amount minus the fee.
            Used when the fee should be included in the transfer amount.
            
        EXCLUSIVE: Fee is charged in addition to the transferred amount.
            The recipient receives the full transferred amount, and the payer
            pays the fee on top of that. Used when the fee should be
            charged separately from the transfer.
    
    Example:
        >>> # Using inclusive fee assessment
        >>> assessment = FeeAssessmentMethod.INCLUSIVE
        >>> print(f"Fee type: {assessment}")
        Fee type: FeeAssessmentMethod.INCLUSIVE
        
        >>> # Using exclusive fee assessment  
        >>> assessment = FeeAssessmentMethod.EXCLUSIVE
        >>> print(f"Fee type: {assessment}")
        Fee type: FeeAssessmentMethod.EXCLUSIVE
    """

    INCLUSIVE = 0
    EXCLUSIVE = 1
