import asyncio
import logging
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.handlers import user, admin, any_text
from bot.middlewares.logging_middleware import LoggingMiddleware
import config


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.update.middleware(LoggingMiddleware())

    dp.include_router(user.router)
    dp.include_router(admin.router)
    dp.include_router(any_text.router)

    await bot.delete_my_commands()
    
    logger.info("Bot started successfully!")
    logger.info(f"Bot username: {(await bot.me()).username}")
    logger.info(f"Admins: {config.ADMIN_TELEGRAM_IDS}")
    
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot stopped with error: {e}")
