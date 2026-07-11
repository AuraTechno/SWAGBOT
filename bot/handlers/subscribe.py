from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timezone
from sqlalchemy import select
from bot.database.db import async_session
from bot.database.models import User as UserModel, Subscription, Payment
from bot.config import config
from bot.keyboards.inline import (
    sub_duration_keyboard,
    sub_users_keyboard,
    back_button,
    main_menu,
    admin_panel_keyboard,
)
from bot.utils.i18n import _
from bot.utils.helpers import calc_end_date, format_date
from bot.utils.menu import safe_edit

router = Router()

_pending_orders = {}


@router.callback_query(F.data == "subscribe")
async def show_duration_selection(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.telegram_id == user_id)
        )
        db_user = result.scalar_one_or_none()
        lang = db_user.language if db_user else "ru"

    await safe_edit(callback,
        _("subscribe.select_duration", lang),
        reply_markup=sub_duration_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sub_dur_"))
async def select_sub_duration(callback: CallbackQuery):
    months = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.telegram_id == user_id)
        )
        db_user = result.scalar_one_or_none()
        lang = db_user.language if db_user else "ru"

    _pending_orders[user_id] = {"months": months}

    await safe_edit(callback,
        _("subscribe.select_users", lang),
        reply_markup=sub_users_keyboard(months, lang),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sub_users_"))
async def select_sub_users(callback: CallbackQuery):
    parts = callback.data.split("_")
    months = int(parts[2])
    users_count = int(parts[3])
    user_id = callback.from_user.id

    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.telegram_id == user_id)
        )
        db_user = result.scalar_one_or_none()
        lang = db_user.language if db_user else "ru"

    price = config.SUBSCRIPTION_OPTIONS.get(months, {}).get(users_count, 0)
    _pending_orders[user_id] = {"months": months, "users": users_count, "price": price}

    text = _("subscribe.confirm", lang, months=months, users_count=users_count, price=price)

    from bot.keyboards.inline import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(
        text=_("subscribe.pay", lang, amount="") + f" {price}₽",
        callback_data=f"sub_pay_{months}_{users_count}"
    )
    builder.button(text=_("buttons.cancel", lang), callback_data="back_to_menu")
    builder.adjust(1)

    await safe_edit(callback,
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sub_pay_"))
async def process_payment(callback: CallbackQuery):
    parts = callback.data.split("_")
    months = int(parts[2])
    users_count = int(parts[3])
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

        price = config.SUBSCRIPTION_OPTIONS.get(months, {}).get(users_count, 0)
        end_date = calc_end_date(months)

        sub = Subscription(
            user_id=db_user.id,
            type="paid",
            duration_months=months,
            users_count=users_count,
            start_date=datetime.now(timezone.utc).replace(tzinfo=None),
            end_date=end_date,
            is_active=True,
        )
        session.add(sub)
        await session.commit()
        await session.refresh(sub)

        if config.REMNAWAVE_TOKEN:
            from bot.services.remnawave import create_user
            username = f"user_{db_user.telegram_id}_sub_{sub.id}"
            remna_result = await create_user(
                username=username,
                expire_days=30 * months,
                email=f"{db_user.telegram_id}@swagvpn.com",
            )
            if remna_result:
                sub.remnawave_uuid = remna_result.get("uuid")
                sub.subscription_url = remna_result.get("subscriptionUrl")
                await session.commit()

        try:
            admin_ids = config.ADMIN_IDS
            for admin_id in admin_ids:
                await callback.bot.send_message(
                    chat_id=admin_id,
                    text=f"💳 Новая оплата!\n\n"
                         f"Пользователь: @{db_user.username or db_user.telegram_id}\n"
                         f"Тариф: {months}мес x{users_count}польз\n"
                         f"Сумма: {price}₽\n"
                         f"Статус: ⏳ Ожидает подтверждения",
                    parse_mode="HTML"
                )
        except Exception:
            pass

    await safe_edit(callback,
        _("subscribe.success", lang, months=months, users_count=users_count, end_date=format_date(end_date)),
        reply_markup=back_button(lang),
        parse_mode="HTML"
    )
    _pending_orders.pop(user_id, None)
    await callback.answer()
