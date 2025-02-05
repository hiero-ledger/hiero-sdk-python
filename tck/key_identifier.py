from hiero_sdk_python import PublicKey, PrivateKey

class KeyIdentifier:

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
