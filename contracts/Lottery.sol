// SPDX-License-Identifier: MIT

pragma solidity ^0.6.6;

import "@chainlink/contracts/src/v0.6/interfaces/AggregatorV3Interface.sol";
import "@chainlink/contracts/src/v0.6/vendor/SafeMathChainlink.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@chainlink/contracts/src/v0.6/VRFConsumerBase.sol";

contract Lottery is VRFConsumerBase, Ownable {
    using SafeMathChainlink for uint256;

    address payable[] public players;
    address payable public recentWinner;
    uint256 public randomness;
    uint256 public usdEntranceFee;
    AggregatorV3Interface internal ETHUSDpriceFeed;
    enum LOTTERY_STATE {
        OPEN,
        CLOSED,
        CALCULATING_WINNER
    } // states equal to 0, 1, 2
    LOTTERY_STATE public lottery_state;
    uint256 public fee;
    bytes32 public keyHash;
    event RequestedRandomness(bytes32 requestID);

    constructor(
        address _priceFeed,
        address _vrfCoordinator,
        address _link,
        uint256 _fee,
        bytes32 _keyHash
    ) public VRFConsumerBase(_vrfCoordinator, _link) {
        usdEntranceFee = 50 * (10**18);
        ETHUSDpriceFeed = AggregatorV3Interface(_priceFeed);
        lottery_state = LOTTERY_STATE.CLOSED; // eguals to lottery_state = 1;
        fee = _fee;
        keyHash = _keyHash;
    }

    function enter() public payable {
        // 50 USD minimum
        require(lottery_state == LOTTERY_STATE.OPEN);
        require(msg.value >= getEntranceFee(), "FUCK YOU POORPLEB");
        players.push(msg.sender);
    }

    function getEntranceFee() public view returns (uint256) {
        (, int256 price, , , ) = ETHUSDpriceFeed.latestRoundData();
        uint256 adjustedPrice = uint256(price) * 10**10; // so you have 18 decimals

        // 50$ / $2000/ETH
        // 50 * 100000 / 2000

        uint256 costToEnter = (usdEntranceFee * 10**18) / adjustedPrice;
        return costToEnter;
    }

    function startLottery() public onlyOwner {
        require(
            lottery_state == LOTTERY_STATE.CLOSED,
            "cant start new lottery yet, because it's currently closed"
        );
        lottery_state = LOTTERY_STATE.OPEN;
    }

    function endLottery() public onlyOwner {
        // FALSE RANDOMNESS:
        // uint256(
        //     keccak256(
        //         abi.encodePacked(
        //             nonce, // nonce is preditable (aka, transaction number)
        //             msg.sender, // msg.sender is predictable
        //             block.difficulty, // can actually be manipulated by the miners!
        //             block.timestamp // timestamp is predictable
        //         )
        //     )
        // ) % players.length;

        // why not require(lottery_state = LOTTERY_STATE.OPEN) ???

        lottery_state = LOTTERY_STATE.CALCULATING_WINNER;
        bytes32 requestID = requestRandomness(keyHash, fee);
        emit RequestedRandomness(requestID);
    }

    //internal because only vrf coordinator can call this function
    function fulfillRandomness(bytes32 _requestId, uint256 _randomness)
        internal
        override
    {
        require(
            lottery_state == LOTTERY_STATE.CALCULATING_WINNER,
            "lottery is still running or hasnt started yet"
        );
        require(_randomness > 0, "random number not found");
        uint256 indexOfWinner = _randomness % players.length; // mod % gives index of winner in a random and fair fashion
        recentWinner = players[indexOfWinner];
        recentWinner.transfer(address(this).balance);
        //reset lottery
        players = new address payable[](0);
        lottery_state = LOTTERY_STATE.CLOSED;
        randomness = _randomness;
    }
}
