from cryptography.hazmat.primitives.asymmetric import ed25519, ec
from hiero_sdk_python import PublicKey, PrivateKey

class KeyIdentifier:

    # NOTE: after having AI try and fail to write this code for a couple tries Im going to give it a crack
    #  to prove that AI isnt better than a 19 year old bum. Also cause they cant do it and im cocky.
    #  So this method will have to do a couple things, it will need to be able to identify from bytes and a string.
    #  Hedera's DER keys seem to be in a hex format
    # TODO: The fact that identify() and is_public() have super similar code is disgusting
    # NOTE: You can probably take some of this code and use it for importing an existing key: https://docs.hedera.com/hedera/sdks-and-apis/sdks/keys/import-an-existing-key

    @classmethod
    def identify(cls, key: str) -> tuple[None | PublicKey | PrivateKey, bool | None]:
        """
        This function will either return a cryptography ...Key object, or it will return None, should not be used
        for anything outside of the TCK code.
        """
        try:
            return PublicKey.from_string(key), True
        except ValueError:
            try:
                return PrivateKey.from_string(key), False
            except ValueError:
                return None, None
