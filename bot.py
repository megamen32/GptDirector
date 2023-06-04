import asyncio
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from handlers import dp


if __name__=='__main__':
    dp.setup_middleware(LoggingMiddleware())
    asyncio.run(dp.start_polling(timeout=70, reset_webhook=False, fast=True))