from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey

from tck.key_identifier import KeyIdentifier


def test_key_identifier():
    assert isinstance(KeyIdentifier().identify("302d300706052b8104000a03220002ffda8e4c9faf6d2b89189196f76c8c6448f7f04e00f56ccff63ba857c2782661"), EllipticCurvePublicKey)