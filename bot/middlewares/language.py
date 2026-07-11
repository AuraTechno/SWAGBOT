from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy import select
from bot.database.db import async_session
from bot.database.models import User as UserModel


class LanguageMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        user = data.get("event_from_user")
        if user:
            try:
                async with async_session() as session:
                    result = await session.execute(
                        select(UserModel).where(UserModel.telegram_id == user.id)
                    )
                    db_user = result.scalar_one_or_none()
                    if db_user:
                        data["lang"] = db_user.language
                    else:
                        data["lang"] = "ru"
            except Exception:
                data["lang"] = "ru"
        else:
            data["lang"] = "ru"

        return await handler(event, data)
