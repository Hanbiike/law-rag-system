"""
Main Telegram bot module.

This module initializes and runs the Telegram bot
using aiogram framework with optimized configuration.
"""
import asyncio
import logging
import sys
from typing import Final

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.handlers import router
from confs.config import TELEGRAM_BOT_TOKEN

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Bot configuration constants
BOT_NAME: Final[str] = "Law RAG Bot"


async def main() -> None:
    """
    Initialize and start the Telegram bot.

    Creates bot instance, dispatcher with memory storage,
    and starts polling for updates.
    
    Raises:
        SystemExit: If TELEGRAM_BOT_TOKEN is not configured.
    """
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set!")
        sys.exit(1)

    # Initialize bot with optimized settings
    bot = Bot(
        token=TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Initialize dispatcher with memory storage
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    logger.info("Starting %s...", BOT_NAME)

    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )
    finally:
        await bot.session.close()


def run_bot() -> None:
    """
    Entry point for running the bot.
    
    Handles keyboard interrupt and exceptions gracefully.
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error("Bot error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    run_bot()
