from aiogram import Bot, Dispatcher
from decouple import config
import openai
TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN')
CHATGPT_API_KEY = config('CHATGPT_API_KEY')
openai.api_key = CHATGPT_API_KEY
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)
