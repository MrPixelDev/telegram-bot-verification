import logging
logging.basicConfig(
    filename='./log/main.log',
    datefmt='%Y-%m-%d %H:%M:%S',
    format='{asctime} - {name} - {levelname:<8} - {message}',
    style='{',
    level=logging.DEBUG
)
logging.getLogger('urllib3').setLevel('WARNING')
logging.getLogger('aiogram').setLevel('WARNING')
logging.getLogger('asyncio').setLevel('WARNING')
logger = logging.getLogger()

from executor import dp
from aiogram.utils import executor
from handlers import client
from data.sqlite_db import start_sql

# _____sqlite3_____

start_sql()

# _____aiogram_____

client.register_handlers_client(dp)

executor.start_polling(dp, skip_updates=True)
