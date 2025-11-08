from hiero_sdk_python import PrivateKey
from hiero_sdk_python.crypto.public_key import PublicKey


def main():
    key = PublicKey.from_string("02fefb27dbd7763ef9f853453ef090500096e8efeba8ec02c6ab3adc0f00ee003c")

    print(key.to_evm_address())

main()