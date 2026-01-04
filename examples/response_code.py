from hiero_sdk_python import ResponseCode


# Mock of a transaction receipt object
class TransactionReceipt:
    def __init__(self, status_code: int):
        self.status = status_code


def response_code(receipt: "TransactionReceipt"):
    status_code = ResponseCode(receipt.status)
    print(f"The response code is {status_code}")

    if status_code == ResponseCode.SUCCESS:
        print("✅ Transaction succeeded!")
    elif status_code.is_unknown:
        print(f"❓ Unknown transaction status: {status_code}")
    else:
        print("❌ Transaction failed!")


def response_name(receipt: "TransactionReceipt"):
    status_code = ResponseCode(receipt.status)
    status_name = status_code.name
    print(f"The response name is {status_name}")

    if status_name == ResponseCode.SUCCESS.name:
        print("✅ Transaction succeeded!")
    elif status_code.is_unknown:
        print(f"❓ Unknown transaction status: {status_name}")
    else:
        print("❌ Transaction failed!")


def main():
    print("=== Receipt Status Demo ===\n")

    # Example 1: Transaction receipt is (SUCCESS)
    receipt_success = TransactionReceipt(ResponseCode.SUCCESS)
    response_code(receipt_success)
    response_name(receipt_success)

    # Example 2: Transaction receipt is (INVALID_SIGNATURE)
    receipt_invalid_signature = TransactionReceipt(ResponseCode.INVALID_SIGNATURE)
    response_code(receipt_invalid_signature)
    response_name(receipt_invalid_signature)

    # Example 3: Unknown status (e.g., 999)
    receipt_unknown_status = TransactionReceipt(999)
    response_code(receipt_unknown_status)
    response_name(receipt_unknown_status)


if __name__ == "__main__":
    main()
