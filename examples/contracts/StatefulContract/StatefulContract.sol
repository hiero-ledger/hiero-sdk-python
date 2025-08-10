pragma solidity ^0.8.2;

contract StatefulContract {
    bytes32 private message;

    address public owner;

    constructor(bytes32 _msg) {
        message = _msg;
        owner = msg.sender;
    }

    function getMessage() external view returns (bytes32) {
        return message;
    }

    function setMessage(bytes32 _msg) external {
        require(msg.sender == owner, "Only the owner can update the message.");
        message = _msg;
    }

    function getMessageAndOwner() external view returns (bytes32, address) {
        return (message, owner);
    }

    function withdrawFunds() external {
        require(msg.sender == owner, "Only the owner can withdraw funds.");
        uint256 amount = address(this).balance;
        payable(owner).transfer(amount);
    }

    receive() external payable {}
}
