from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, ChatMemberUpdated
from aiogram.enums import ChatMemberStatus
from bot.config import config
from bot.utils.i18n import _

import logging

logger = logging.getLogger(__name__)


class ChannelSubscriptionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        if not config.REQUIRED_CHANNEL_ID:
            return await handler(event, data)

        user = data.get("event_from_user")
        bot = data.get("bot")

        if not user or not bot:
            return await handler(event, data)

        try:
            chat_member = await bot.get_chat_member(
                chat_id=config.REQUIRED_CHANNEL_ID,
                user_id=user.id
            )
            if chat_member.status in (
                ChatMemberStatus.LEFT,
                ChatMemberStatus.KICKED,
                ChatMemberStatus.RESTRICTED,
            ):
                from bot.keyboards.reply import channel_subscribe_keyboard
                from bot.database.db import async_session
                from bot.database.models import User as UserModel
                from sqlalchemy import select

                lang = "ru"
                async with async_session() as session:
                    result = await session.execute(
                        select(UserModel).where(UserModel.telegram_id == user.id)
                    )
                    db_user = result.scalar_one_or_none()
                    if db_user:
                        lang = db_user.language

                text = _("channel.must_subscribe", lang, channel_url=config.REQUIRED_CHANNEL_URL)
                if hasattr(event, "message") and event.message:
                    await event.message.answer(
                        text,
                        reply_markup=channel_subscribe_keyboard(config.REQUIRED_CHANNEL_URL, lang),
                        disable_web_page_preview=True
                    )
                return
        except Exception as e:
            logger.warning(f"Channel subscription check failed: {e}")

        return await handler(event, data)
