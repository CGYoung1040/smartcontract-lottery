# integration test on testnet

from brownie import Lottery, accounts, config, network, exceptions
from scripts.deploy_lottery import deploy_lottery
from scripts.helpful_scripts import (
    get_account,
    fund_with_link,
    get_contract,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
)
from web3 import Web3
import pytest
import time


def test_can_pick_winner():
    # Arrange
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    fund_with_link(lottery.address)
    starting_balance_of_account = account.balance()
    balance_of_lottery = lottery.balance()
    # Act
    transaction = lottery.endLottery({"from": account})
    time.sleep(180)

    # Assert
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0

    # assert account.balance() == starting_balance_of_account + balance_of_lottery
