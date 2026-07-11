import logging
from datetime import datetime, timezone
from sqlalchemy import select
from bot.database.db import async_session
from bot.database.models import Subscription, User as UserModel
from bot.utils.i18n import _
from bot.utils.helpers import format_date

logger = logging.getLogger(__name__)


async def check_expiring_subscriptions(bot):
    now = datetime.now(timezone.utc)
    async with async_session() as session:
        result = await session.execute(
            select(Subscription).where(
                Subscription.is_active == True,
                Subscription.end_date > now
            )
        )
        subs = result.scalars().all()

        for sub in subs:
            remaining_days = (sub.end_date - now).days
            if remaining_days in [7, 3, 1]:
                user_result = await session.execute(
                    select(UserModel).where(UserModel.id == sub.user_id)
                )
                db_user = user_result.scalar_one_or_none()
                if not db_user:
                    continue

                lang = db_user.language
                try:
                    await bot.send_message(
                        chat_id=db_user.telegram_id,
                        text=_("notifications.expiring_soon", lang,
                               days=remaining_days,
                               date=format_date(sub.end_date)),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.warning(f"Failed to notify user {db_user.telegram_id}: {e}")

        expired_result = await session.execute(
            select(Subscription).where(
                Subscription.is_active == True,
                Subscription.end_date <= now
            )
        )
        expired_subs = expired_result.scalars().all()
        for sub in expired_subs:
            sub.is_active = False
            user_result = await session.execute(
                select(UserModel).where(UserModel.id == sub.user_id)
            )
            db_user = user_result.scalar_one_or_none()
            if db_user:
                try:
                    await bot.send_message(
                        chat_id=db_user.telegram_id,
                        text=_("notifications.expired", db_user.language),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.warning(f"Failed to notify user {db_user.telegram_id}: {e}")

        await session.commit()
