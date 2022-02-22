from brownie import Lottery, network, config, MockV3Aggregator
from scripts.helpful_scripts import (
    get_account,
    deploy_mocks,
    get_contract,
    fund_with_link,
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
)
import time

BLOCK_CONFIRMATIONS_FOR_VERIFICATION = 5


def deploy_lottery():
    account = get_account()
    lottery = Lottery.deploy(
        get_contract("eth_usd_price_feed").address,
        get_contract("vrf_coordinator").address,
        get_contract("link_token").address,
        config["networks"][network.show_active()]["fee"],
        config["networks"][network.show_active()]["keyhash"],
        {"from": account},
        # publish_source=config["networks"][network.show_active()].get(
        #    "verify", False
        # ),  # if theres no key for verify, set it to false
    )

    # https://github.com/PatrickAlphaC/smartcontract-lottery/issues/41
    # https://github.com/smartcontractkit/chainlink-mix/blob/main/scripts/vrf_scripts/01_deploy_vrf.py

    if config["networks"][network.show_active()].get("verify", False):
        lottery.tx.wait(5)
        Lottery.publish_source(lottery)
    else:
        lottery.tx.wait(1)

    print(f"Lottery contract has been deployed to {lottery.address}")
    return lottery


def start_lottery():
    account = get_account()
    lottery = Lottery[-1]
    starting_tx = lottery.startLottery({"from": account})
    starting_tx.wait(1)
    print("Lottery started")


def enter_lottery():
    account = get_account()
    lottery = Lottery[-1]
    value = lottery.getEntranceFee()  # + 100000000
    tx = lottery.enter({"from": account, "value": value})
    tx.wait(1)
    print("Lottery entered")


def end_lottery():
    account = get_account()
    lottery = Lottery[-1]
    # fund contract with LINK token (common function - helpful scripts)
    # then end lottery
    tx = fund_with_link(lottery.address)
    tx.wait(1)
    ending_tx = lottery.endLottery({"from": account})
    ending_tx.wait(1)
    time.sleep(60)
    print(
        f"{lottery.recentWinner()} is the winner of this lottery"
    )  # WHY lottery.recentWinner() and not lottery.recentWinner (since it's not a function I'm calling)???


def main():
    deploy_lottery()
    start_lottery()
    enter_lottery()
    end_lottery()
