from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage, RedisStorage2
from decouple import config
import openai
TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN')
CHATGPT_API_KEY = config('CHATGPT_API_KEY')
openai.api_key = CHATGPT_API_KEY
bot = Bot(token=TELEGRAM_BOT_TOKEN)
storage=RedisStorage2()
dp = Dispatcher(bot,storage=storage)
