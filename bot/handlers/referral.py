from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select, func
from bot.database.db import async_session
from bot.database.models import User as UserModel, Referral
from bot.keyboards.inline import back_button
from bot.utils.i18n import _
from bot.config import config
from bot.utils.menu import safe_edit_text

router = Router()


@router.callback_query(F.data == "referral")
async def show_referral(callback: CallbackQuery):
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

        ref_count_result = await session.execute(
            select(func.count()).select_from(Referral).where(
                Referral.referrer_id == db_user.telegram_id
            )
        )
        ref_count = ref_count_result.scalar() or 0

    bot_username = (await callback.bot.me()).username
    ref_link = f"https://t.me/{bot_username}?start=ref_{db_user.referral_code}"

    text = _("referral.title", lang) + "\n\n"
    text += _("referral.your_link", lang, link=ref_link) + "\n\n"
    text += _("referral.invited", lang, count=ref_count) + "\n"
    text += _("referral.reward", lang, days=config.REFERRAL_BONUS_DAYS)

    await safe_edit_text(callback,
        text,
        reply_markup=back_button(lang),
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    await callback.answer()
