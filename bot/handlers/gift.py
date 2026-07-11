from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timezone
from sqlalchemy import select
from bot.database.db import async_session
from bot.database.models import User as UserModel, GiftCode, Subscription
from bot.config import config
from bot.keyboards.inline import back_button
from bot.utils.i18n import _
from bot.utils.helpers import calc_end_date, format_date
from bot.utils.menu import safe_edit

router = Router()


class GiftActivation(StatesGroup):
    waiting_for_code = State()


@router.callback_query(F.data == "gift")
async def start_gift(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.telegram_id == user_id)
        )
        db_user = result.scalar_one_or_none()
        lang = db_user.language if db_user else "ru"

    await safe_edit(callback,
        _("gift.enter_code", lang),
        reply_markup=back_button(lang),
        parse_mode="HTML"
    )
    await state.set_state(GiftActivation.waiting_for_code)
    await callback.answer()


@router.message(GiftActivation.waiting_for_code)
async def process_gift_code(message: Message, state: FSMContext):
    code_str = message.text.strip().upper()
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.telegram_id == user_id)
        )
        db_user = result.scalar_one_or_none()
        lang = db_user.language if db_user else "ru"

        gift_result = await session.execute(
            select(GiftCode).where(GiftCode.code == code_str, GiftCode.is_active == True)
        )
        gift = gift_result.scalar_one_or_none()

        if not gift:
            await message.answer(
                _("gift.invalid", lang),
                reply_markup=back_button(lang),
                parse_mode="HTML"
            )
            await state.clear()
            return

        if gift.used_count >= gift.max_uses:
            await message.answer(
                _("gift.expired", lang),
                reply_markup=back_button(lang),
                parse_mode="HTML"
            )
            await state.clear()
            return

        end_date = calc_end_date(gift.duration_months)
        sub = Subscription(
            user_id=db_user.id,
            type="gift",
            duration_months=gift.duration_months,
            users_count=gift.users_count,
            start_date=datetime.now(timezone.utc).replace(tzinfo=None),
            end_date=end_date,
            is_active=True,
        )
        session.add(sub)
        await session.flush()
        await session.refresh(sub)

        if config.REMNAWAVE_TOKEN:
            from bot.services.remnawave import create_user
            username = f"user_{db_user.telegram_id}_gift_{sub.id}"
            remna_result = await create_user(
                username=username,
                expire_days=30 * gift.duration_months,
                email=f"{db_user.telegram_id}@swagvpn.com",
            )
            if remna_result:
                sub.remnawave_uuid = remna_result.get("uuid")
                sub.subscription_url = remna_result.get("subscriptionUrl")

        gift.used_count += 1
        if gift.used_count >= gift.max_uses:
            gift.is_active = False
        await session.commit()

    await message.answer(
        _("gift.success", lang, months=gift.duration_months, users_count=gift.users_count),
        reply_markup=back_button(lang),
        parse_mode="HTML"
    )
    await state.clear()
