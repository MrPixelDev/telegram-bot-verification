import logging

import data.messages
from data.sqlite_db import fetch_tx, refill_balance
import pyqiwi
from pyqiwi.exceptions import APIError
from environs import Env
from datetime import datetime, timedelta, timezone

env = Env()
env.read_env(".env")


# ##-----------------------------------------------------------------
# Choosing alive wallet
# ##-----------------------------------------------------------------
def choose_wallet(i, wlt):
    qiwi_api_key = env.str(f"QIWI_API_KEY_{i}")
    qiwi_number = env.str(f"QIWI_NUMBER_{i}")
    qiwi_card = env.str(f"QIWI_CARD_{i}")
    try:
        wlt = pyqiwi.Wallet(token=qiwi_api_key, number=qiwi_number)
        if wlt.profile.contract_info.blocked:
            logging.warning(f"+{qiwi_number} is blocked")
            return None
        else:
            logging.warning(f"+{qiwi_number} connected.")
    except APIError as e:
        logging.warning(f"+{qiwi_number}: {e}")
    if wlt is not None:
        data.messages.wallet_num = qiwi_number
        data.messages.wallet_card = qiwi_card
    return wlt


def is_active_wallet():
    i = 0
    wlt = None
    while i < 3 and wlt is None:
        i += 1
        wlt = choose_wallet(i, wlt)
    return wlt


wallet = is_active_wallet()


# ##-----------------------------------------------------------------
# Get balance of current wallet
# ##-----------------------------------------------------------------
def get_balance():
    return wallet.accounts[0].balance['amount']


logging.warning(get_balance())
# ##-----------------------------------------------------------------
# Get history of trx from past 2 days
# ##-----------------------------------------------------------------
async def get_history():
    tzinfo = timezone(timedelta(hours=11))
    end_date = datetime.now(tzinfo)
    start_date = end_date - timedelta(days=2)
    try:
        return wallet.history(operation="IN", start_date=start_date, end_date=end_date)
    except AttributeError as e:
        logging.error(e)
        return 0


# ##-----------------------------------------------------------------
# Registering new TX
# ##-----------------------------------------------------------------
async def new_tx(transaction):
    txn_id = transaction.txn_id
    date = str(transaction.date)[:-6]
    status = transaction.status
    txn_type = transaction.type
    amount = transaction.sum.amount
    user_id = int(transaction.comment) - 7
    data_tuple = (txn_id, date, status, txn_type, amount, user_id)
    logging.warning(f"Data tuple for new tx created.\n{data_tuple}")
    await refill_balance(data_tuple)


# ##-----------------------------------------------------------------
# Check for incomes
# ##-----------------------------------------------------------------
async def find_tx(comment: int):
    history = await get_history()
    if history != 0:
        for transaction in history['transactions']:
            if transaction.comment == str(comment):
                txn_id = transaction.txn_id
                if await fetch_tx(txn_id) is None:
                    await new_tx(transaction)


# ##-----------------------------------------------------------------
# Refill by command
# ##-----------------------------------------------------------------
async def refill_smsvf(recipient, amount, uid):
    try:
        tx = wallet.send("99", recipient, amount, uid)
        logging.warning(f"Wallet successfully refilled")
        return tx
    except APIError as e:
        logging.error(e.response)
        return None
