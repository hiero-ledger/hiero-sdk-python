pragma solidity ^0.8.2;

contract ConstructorTestContract {
    string private messageString;
    bytes32 private messageBytes32;
    int8 private messageInt8;
    address private messageAddress;
    bool private messageBool;
    bytes private messageBytes;
    uint8[] private messageUint8Array;

    constructor(string memory _msgString, bytes32 _msgBytes32, int8 _msgInt8, address _msgAddress, bool _msgBool, bytes memory _msgBytes, uint8[] memory _msgUint8Array) {
        messageString = _msgString;
        messageBytes32 = _msgBytes32;
        messageInt8 = _msgInt8;
        messageAddress = _msgAddress;
        messageBool = _msgBool;
        messageBytes = _msgBytes;
        messageUint8Array = _msgUint8Array;
    }
}
