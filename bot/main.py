import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import config
from bot.database.db import init_db
from bot.utils.i18n import load_localizations

from bot.handlers import start, profile, subscribe, trial, referral, gift, admin
from bot.middlewares.language import LanguageMiddleware

from bot.services.notifications import check_expiring_subscriptions

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def scheduler(bot: Bot):
    while True:
        try:
            await check_expiring_subscriptions(bot)
        except Exception as e:
            logger.error(f"Notification check failed: {e}")
        await asyncio.sleep(config.NOTIFICATION_CHECK_INTERVAL_HOURS * 3600)


async def main():
    logger.info("Starting SWAG VPN Bot...")

    load_localizations()

    await init_db(reset=False)

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.update.middleware(LanguageMiddleware())

    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(trial.router)
    dp.include_router(subscribe.router)
    dp.include_router(referral.router)
    dp.include_router(gift.router)
    dp.include_router(admin.router)

    asyncio.create_task(scheduler(bot))

    logger.info(f"Bot started: @{(await bot.me()).username}")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
