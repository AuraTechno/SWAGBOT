from aiogram import Router, F
from aiogram.types import CallbackQuery
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from bot.database.db import async_session
from bot.database.models import User as UserModel, Subscription
from bot.config import config
from bot.keyboards.inline import trial_keyboard, back_button
from bot.utils.i18n import _
from bot.utils.helpers import format_date, calc_end_date
from bot.utils.menu import safe_edit

router = Router()


@router.callback_query(F.data == "trial")
async def show_trial(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.telegram_id == user_id)
        )
        db_user = result.scalar_one_or_none()
        if not db_user:
            await callback.answer()
            return
        lang = db_user.language

    await safe_edit(callback,
        _("trial.title", lang),
        reply_markup=trial_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "activate_trial")
async def activate_trial(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.telegram_id == user_id)
        )
        db_user = result.scalar_one_or_none()
        if not db_user:
            await callback.answer()
            return
        lang = db_user.language

        trial_result = await session.execute(
            select(func.count()).select_from(Subscription).where(
                Subscription.user_id == db_user.id,
                Subscription.type == "trial"
            )
        )
        trial_count = trial_result.scalar() or 0

        if trial_count > 0:
            await safe_edit(callback,
                _("trial.already_used", lang),
                reply_markup=back_button(lang),
                parse_mode="HTML"
            )
            await callback.answer()
            return

        active_sub = await session.execute(
            select(Subscription).where(
                Subscription.user_id == db_user.id,
                Subscription.is_active == True
            ).limit(1)
        )
        if active_sub.scalar_one_or_none():
            await safe_edit(callback,
                _("trial.has_subscription", lang),
                reply_markup=back_button(lang),
                parse_mode="HTML"
            )
            await callback.answer()
            return

        end_date = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=config.TRIAL_DAYS)
        sub = Subscription(
            user_id=db_user.id,
            type="trial",
            duration_months=0,
            users_count=config.TRIAL_MAX_USERS,
            start_date=datetime.now(timezone.utc).replace(tzinfo=None),
            end_date=end_date,
            is_active=True,
        )
        session.add(sub)
        await session.commit()

    await safe_edit(callback,
        _("trial.success", lang, end_date=format_date(end_date)),
        reply_markup=back_button(lang),
        parse_mode="HTML"
    )
    await callback.answer()
