import asyncio

import aiogram
import openai
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from handlers import dp


if __name__=='__main__':
    dp.setup_middleware(LoggingMiddleware())
    proxy = 'http://168.80.203.204:8000'
    openai.proxy={'http':proxy,'https':proxy}
    aiogram.executor.start_polling(dp,timeout=70, reset_webhook=False, fast=False)