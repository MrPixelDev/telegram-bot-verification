import logging

import json.decoder
import sqlite3 as sq
from API.SMS_API import get_sms_code
from random import randint


# ##-----------------------------------------------------------------
# Starting SQLite, checking db and tables
# ##-----------------------------------------------------------------
def start_sql():
    users_base = sq.connect('users.db')
    users_cur = users_base.cursor()

    if users_base:
        logging.warning("SQLite3 started successfully.")

    users_cur.execute("CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, "
                      "balance FLOAT)")
    users_base.commit()
    users_cur.execute("CREATE TABLE IF NOT EXISTS numbers(idNum TEXT, "
                      "chat TEXT, "
                      "country TEXT, "
                      "svc TEXT, "
                      "num INTEGER, "
                      "price FLOAT, "
                      "sms TEXT, "
                      "id TEXT, "
                      "is_active BOOLEAN, "
                      "FOREIGN KEY (id) REFERENCES users (id) ON DELETE CASCADE ON UPDATE NO ACTION)")
    users_base.commit()
    users_cur.execute("CREATE TABLE IF NOT EXISTS tx(txn_id INTEGER PRIMARY KEY, "
                      "date TEXT, "
                      "status TEXT, "
                      "type TEXT, "
                      "amount FLOAT, "
                      "id TEXT, "
                      "FOREIGN KEY (id) REFERENCES users (id) ON DELETE CASCADE ON UPDATE NO ACTION)")
    users_base.commit()


# ##-----------------------------------------------------------------
# Adding new user
# ##-----------------------------------------------------------------
async def new_user(query):
    user_id = query.chat.id
    users_base = sq.connect('users.db')
    users_cur = users_base.cursor()
    users_cur.execute(f"SELECT id FROM users WHERE id = '{user_id}'")
    data = users_cur.fetchone()
    if data is None:
        data_tuple = (user_id, 0.0)
        users_cur.execute("INSERT INTO users VALUES(?, ?);", data_tuple)
        users_base.commit()

        logging.warning(f"User {user_id} added to DB")


# ##-----------------------------------------------------------------
# Delete something
# ##-----------------------------------------------------------------
async def del_user(userid):
    base = sq.connect('users.db')
    cur = base.cursor()
    cur.execute(f"UPDATE users SET num = 791395574831 WHERE id = {userid}")
    base.commit()


# ##-----------------------------------------------------------------
# Fetching active numbers
# ##-----------------------------------------------------------------
async def show_balance(userid):
    users_base = sq.connect('users.db')
    users_cur = users_base.cursor()
    users_cur.execute(f"SELECT users.balance FROM users WHERE id = '{userid}'")
    balance = users_cur.fetchone()
    return balance[0]


# ##-----------------------------------------------------------------
# Fetching active numbers
# ##-----------------------------------------------------------------
async def fetch_active_nums(query):
    users_base = sq.connect('users.db')
    users_cur = users_base.cursor()
    users_cur.execute(f"SELECT numbers.num, numbers.idNum, numbers.svc "
                      f"FROM numbers "
                      f"WHERE numbers.id='{query.from_user.id}'")
    nums = users_cur.fetchall()
    numbers = []
    for row in nums:
        if len(row) > 0:
            try:
                code = await get_sms_code(idnum=row[1])
                if list(code.values())[0] == 'idNumNotFound':
                    users_cur.execute(f"DELETE FROM numbers WHERE idNum = '{row[1]}'")
                    users_base.commit()
                else:
                    numbers.append(row)
            except json.decoder.JSONDecodeError:
                users_cur.execute(f"DELETE FROM numbers WHERE idNum = '{row[1]}'")
                users_base.commit()
    return numbers


# ##-----------------------------------------------------------------
# Set region while taking new number
# ##-----------------------------------------------------------------
async def set_region(query, region_code):
    chat = query.message.chat.id
    user_id = query.from_user.id
    users_base = sq.connect('users.db')
    users_cur = users_base.cursor()
    idnum = randint(100000, 999999)
    data_tuple = (idnum, chat, region_code, None, None, 0.0, None, user_id, True)
    users_cur.execute("INSERT INTO numbers VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", data_tuple)
    users_base.commit()


async def return_region(query, service_code):
    chat = query.message.chat.id
    users_base = sq.connect('users.db')
    users_cur = users_base.cursor()
    users_cur.execute(f"SELECT numbers.country FROM numbers "
                      f"WHERE numbers.svc = '{service_code}' "
                      f"AND numbers.chat = '{chat}' "
                      f"AND numbers.is_active = 1")
    region = users_cur.fetchone()
    return region[0]


# ##-----------------------------------------------------------------
# Set service while taking new number
# ##-----------------------------------------------------------------
async def set_service(query, service):
    chat = query.message.chat.id
    users_base = sq.connect('users.db')
    users_cur = users_base.cursor()
    users_cur.execute(f"UPDATE numbers SET svc = '{service}' "
                      f"WHERE numbers.num IS NULL "
                      f"AND numbers.chat = '{chat}' "
                      f"AND numbers.is_active = 1")
    users_base.commit()


# ##-----------------------------------------------------------------
# Add new number
# ##-----------------------------------------------------------------
async def new_number(query, tel, price):
    chat = query.message.chat.id
    idnum = tel['idNum']
    num = tel['tel']
    users_base = sq.connect('users.db')
    users_cur = users_base.cursor()
    users_cur.execute(f"UPDATE numbers SET idNum = '{idnum}', num = '{num}', price = '{price}'"
                      f"WHERE numbers.num IS NULL "
                      f"AND numbers.chat = '{chat}' "
                      f"AND numbers.is_active = 1")
    users_base.commit()


# ##-----------------------------------------------------------------
# Fetch idNum
# ##-----------------------------------------------------------------
async def return_idnum(query, num):
    await fetch_active_nums(query)
    chat = query.message.chat.id
    users_base = sq.connect('users.db')
    users_cur = users_base.cursor()
    users_cur.execute(f"SELECT numbers.idNum FROM numbers "
                      f"WHERE numbers.chat = '{chat}' "
                      f"AND numbers.num = '{num}' "
                      f"AND numbers.is_active = 1")
    idnum = users_cur.fetchone()
    return idnum[0]


# ##-----------------------------------------------------------------
# Add new sms to number
# ##-----------------------------------------------------------------
async def new_sms(idnum, code):
    users_base = sq.connect('users.db')
    users_cur = users_base.cursor()
    users_cur.execute(f"UPDATE numbers SET sms = '{code}', is_active = 0 "
                      f"WHERE numbers.idNum = '{idnum}'")
    users_base.commit()


# ##-----------------------------------------------------------------
# Deactivating Number in DB
# ##-----------------------------------------------------------------
async def deactivate_num(idnum):
    users_base = sq.connect('users.db')
    users_cur = users_base.cursor()
    users_cur.execute(f"UPDATE numbers SET is_active = 0 WHERE numbers.idNum = '{idnum}'")
    users_base.commit()


async def return_price(idnum, num):
    users_base = sq.connect('users.db')
    users_cur = users_base.cursor()
    users_cur.execute(f"SELECT price FROM numbers WHERE idNum = '{idnum}' AND num = '{num}' AND is_active = 1")
    price = users_cur.fetchone()
    users_base.commit()
    return price[0]


# ##-----------------------------------------------------------------
# Update balance
# ##-----------------------------------------------------------------
async def update_balance(userid, delta):
    users_base = sq.connect('users.db')
    users_cur = users_base.cursor()
    users_cur.execute(f"SELECT balance FROM users WHERE users.id = '{userid}'")
    old_balance = users_cur.fetchone()
    new_balance = old_balance[0] + delta
    users_cur.execute(f"UPDATE users SET balance = '{new_balance}' WHERE users.id = '{userid}'")
    users_base.commit()


# ##-----------------------------------------------------------------
# Find transaction
# ##-----------------------------------------------------------------
async def fetch_tx(txn_id):
    users_base = sq.connect('users.db')
    users_cur = users_base.cursor()
    users_cur.execute(f"SELECT txn_id FROM tx WHERE txn_id = '{txn_id}'")
    txn = users_cur.fetchone()
    return txn


# ##-----------------------------------------------------------------
# On Refill balance
# ##-----------------------------------------------------------------
async def refill_balance(data_tuple):
    users_base = sq.connect('users.db')
    users_cur = users_base.cursor()
    users_cur.execute(f"INSERT INTO tx VALUES(?, ?, ?, ?, ?, ?)", data_tuple)
    users_base.commit()
    userid = data_tuple[5]
    delta = data_tuple[4]
    await update_balance(userid, delta)
