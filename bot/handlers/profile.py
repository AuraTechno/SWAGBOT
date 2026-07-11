from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select, func
from bot.database.db import async_session
from bot.database.models import User as UserModel, Subscription, Referral
from bot.keyboards.inline import back_button
from bot.utils.i18n import _
from bot.utils.helpers import format_date

router = Router()


@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.telegram_id == user_id)
        )
        db_user = result.scalar_one_or_none()
        if not db_user:
            await callback.answer("User not found", show_alert=True)
            return

        lang = db_user.language

        active_sub = await session.execute(
            select(Subscription).where(
                Subscription.user_id == db_user.id,
                Subscription.is_active == True
            ).order_by(Subscription.end_date.desc())
        )
        sub = active_sub.scalars().first()

        ref_count_result = await session.execute(
            select(func.count()).select_from(Referral).where(
                Referral.referrer_id == db_user.telegram_id
            )
        )
        ref_count = ref_count_result.scalar() or 0

        trial_used_result = await session.execute(
            select(func.count()).select_from(Subscription).where(
                Subscription.user_id == db_user.id,
                Subscription.type == "trial"
            )
        )
        trial_used = trial_used_result.scalar() or 0

    if sub:
        sub_status = _("profile.active", lang, date=format_date(sub.end_date))
        users_info = _("profile.users_count", lang, count=sub.users_count)
    else:
        sub_status = _("profile.no_active", lang)
        users_info = ""

    trial_text = _("profile.trial_used", lang, used="✅" if trial_used > 0 else "❌")

    text = _("profile.title", lang) + "\n\n"
    text += _("profile.id", lang, telegram_id=user_id) + "\n"
    if db_user.username:
        text += _("profile.username", lang, username=db_user.username) + "\n"
    text += f"{sub_status}\n"
    if users_info:
        text += f"{users_info}\n"
    text += f"{trial_text}\n\n"
    if db_user.referral_code:
        text += _("profile.referral_code", lang, code=db_user.referral_code) + "\n"
    text += _("profile.referral_count", lang, count=ref_count)

    await callback.message.edit_text(
        text,
        reply_markup=back_button(lang),
        parse_mode="HTML"
    )
    await callback.answer()
