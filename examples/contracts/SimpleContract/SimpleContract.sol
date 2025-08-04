pragma solidity ^0.8.2;

contract SimpleContract {
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    function greet() public pure returns (string memory) {
        return "Hello, world!";
    }

    function withdrawFunds() public {
        require(msg.sender == owner, "Only the owner can withdraw funds.");
        uint256 amount = address(this).balance;
        payable(owner).transfer(amount);
    }

    receive() external payable {}
}