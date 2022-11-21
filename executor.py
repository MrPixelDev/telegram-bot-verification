from environs import Env
from aiogram import Bot
from aiogram.dispatcher import Dispatcher

env = Env()
env.read_env(".env")
TST_API_TOKEN = env.str("TST_API_TOKEN")
bot = Bot(TST_API_TOKEN)
dp = Dispatcher(bot)
