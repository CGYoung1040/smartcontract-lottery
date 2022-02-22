# UNIT tests on local environment - development

# expect to get 0.0161 ETH ($3100/ETH) = 161000000000000000 wei
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


""" def test_get_entrance_fee():
    account = accounts[0]
    price_feed_address = config["networks"][network.show_active()]["eth_usd_price_feed"]
    lottery = Lottery.deploy(
        price_feed_address,
        {"from": account},
    )


    assert lottery.getEntranceFee() >= Web3.toWei(0.015, "ether")
    assert lottery.getEntranceFee() <= Web3.toWei(0.022, "ether") """


# since its a unit test, we wanna run on a local environment
def test_get_entrance_fee():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # accounts = get_account() # not needed
    # Arrange
    lottery = deploy_lottery()
    # Act
    # 2900 ETH Price - 2000 wegen initial value bei deploy mocks
    # usd entry fee is $50
    # 50/2900
    entrance_fee = lottery.getEntranceFee()
    expected_entrance_fee = Web3.toWei(
        (50 / 2000), "ether"
    )  # 2000 wegen initial value when deploying mocks?
    # Assert
    assert expected_entrance_fee == entrance_fee


def test_cant_enter_unless_started():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    # Act / Assert
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from": get_account(), "value": lottery.getEntranceFee()})


def test_can_start_and_enter_lottery():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    # Act
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    # Assert
    assert lottery.lottery_state() == 0
    assert lottery.players(0) == account


def test_can_end_lottery():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    tx = fund_with_link(lottery.address)
    tx.wait(1)
    # Act
    lottery.endLottery({"from": account})
    # Assert
    assert lottery.lottery_state() == 2  # 2 means calculating.winner
    # assert len(lottery.players()) == 0 # test if players array has been reset (kommt in den naechsten test)


def test_can_pick_winner_correctly():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=1), "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=2), "value": lottery.getEntranceFee()})
    # lottery.enter({"from": get_account(index=3), "value": lottery.getEntranceFee()})
    fund_with_link(lottery.address)
    starting_balance_of_account = account.balance()
    balance_of_lottery = lottery.balance()
    # Act
    transaction = lottery.endLottery({"from": account})
    request_id = transaction.events["RequestedRandomness"]["requestID"]
    STATIC_RNG = 777
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, STATIC_RNG, lottery.address, {"from": account}
    )

    # Assert
    # 777 % 3 = 0 - index 0 wins = account
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0
    assert account.balance() == starting_balance_of_account + balance_of_lottery
