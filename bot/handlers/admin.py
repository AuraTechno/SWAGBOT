import asyncio
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, func
from bot.database.db import async_session, reset_database
from bot.database.models import User as UserModel, Subscription, Payment, Admin as AdminModel, GiftCode
from bot.config import config
from bot.keyboards.inline import admin_panel_keyboard, back_button, main_menu
from bot.utils.i18n import _
from bot.utils.helpers import generate_gift_code, format_date
from bot.utils.menu import safe_edit

logging = __import__("logging").getLogger(__name__)

router = Router()


class MailingState(StatesGroup):
    waiting_for_message = State()


class CreateGiftState(StatesGroup):
    waiting_for_months = State()
    waiting_for_users = State()
    waiting_for_max_uses = State()


def is_admin(tg_id: int) -> bool:
    return tg_id in config.ADMIN_IDS


@router.callback_query(F.data == "admin_panel")
async def admin_panel(callback: CallbackQuery):
    user_id = callback.from_user.id
    if not is_admin(user_id):
        await callback.answer(_("errors.not_admin", "ru"), show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.telegram_id == user_id)
        )
        db_user = result.scalar_one_or_none()
        lang = db_user.language if db_user else "ru"

    await safe_edit(callback,
        _("admin.panel", lang),
        reply_markup=admin_panel_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    user_id = callback.from_user.id
    if not is_admin(user_id):
        return

    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.telegram_id == user_id)
        )
        db_user = result.scalar_one_or_none()
        lang = db_user.language if db_user else "ru"

        total_users = await session.execute(select(func.count()).select_from(UserModel))
        total_users = total_users.scalar() or 0

        active_subs = await session.execute(
            select(func.count()).select_from(Subscription).where(Subscription.is_active == True)
        )
        active_subs = active_subs.scalar() or 0

        total_payments = await session.execute(
            select(func.count()).select_from(Payment).where(Payment.status == "completed")
        )
        total_payments = total_payments.scalar() or 0

        revenue_result = await session.execute(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.status == "completed")
        )
        revenue = revenue_result.scalar() or 0

    text = _("admin.stats", lang,
             total_users=total_users,
             active_subs=active_subs,
             total_payments=total_payments,
             revenue=round(revenue, 2))

    await safe_edit(callback,
        text,
        reply_markup=admin_panel_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_create_gift")
async def admin_create_gift_start(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if not is_admin(user_id):
        return
    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.telegram_id == user_id)
        )
        db_user = result.scalar_one_or_none()
        lang = db_user.language if db_user else "ru"

    await safe_edit(callback,
        "📝 Введи срок подписки в месяцах (1, 3, 6, 12):",
        reply_markup=back_button(lang),
        parse_mode="HTML"
    )
    await state.set_state(CreateGiftState.waiting_for_months)
    await callback.answer()


@router.message(CreateGiftState.waiting_for_months)
async def process_gift_months(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not is_admin(user_id):
        return
    try:
        months = int(message.text.strip())
        if months not in [1, 3, 6, 12]:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введи 1, 3, 6 или 12:")
        return

    await state.update_data(months=months)
    await message.answer("👥 Введи количество пользователей (1-4):")
    await state.set_state(CreateGiftState.waiting_for_users)


@router.message(CreateGiftState.waiting_for_users)
async def process_gift_users(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not is_admin(user_id):
        return
    try:
        users = int(message.text.strip())
        if users < 1 or users > 4:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введи число от 1 до 4:")
        return

    await state.update_data(users=users)
    await message.answer("🔄 Введи максимальное количество использований:")
    await state.set_state(CreateGiftState.waiting_for_max_uses)


@router.message(CreateGiftState.waiting_for_max_uses)
async def process_gift_max_uses(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not is_admin(user_id):
        return
    try:
        max_uses = int(message.text.strip())
        if max_uses < 1:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введи положительное число:")
        return

    data = await state.get_data()
    months = data["months"]
    users = data["users"]
    code = generate_gift_code()

    async with async_session() as session:
        gift = GiftCode(
            code=code,
            duration_months=months,
            users_count=users,
            max_uses=max_uses,
            created_by=user_id,
        )
        session.add(gift)
        await session.commit()

    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.telegram_id == user_id)
        )
        db_user = result.scalar_one_or_none()
        lang = db_user.language if db_user else "ru"

    await message.answer(
        _("admin.gift_created", lang,
          code=code, months=months, users=users, max_uses=max_uses),
        reply_markup=admin_panel_keyboard(lang),
        parse_mode="HTML"
    )
    await state.clear()


@router.callback_query(F.data == "admin_mailing")
async def admin_mailing_start(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if not is_admin(user_id):
        return
    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.telegram_id == user_id)
        )
        db_user = result.scalar_one_or_none()
        lang = db_user.language if db_user else "ru"

    await safe_edit(callback,
        "📨 Введи текст рассылки (поддерживается HTML):",
        reply_markup=back_button(lang),
        parse_mode="HTML"
    )
    await state.set_state(MailingState.waiting_for_message)
    await callback.answer()


@router.message(MailingState.waiting_for_message)
async def process_mailing(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not is_admin(user_id):
        return

    text = message.html_text or message.text
    async with async_session() as session:
        result = await session.execute(select(UserModel))
        users = result.scalars().all()

    sent = 0
    failed = 0
    bot = message.bot
    for user in users:
        try:
            await bot.send_message(
                chat_id=user.telegram_id,
                text=text,
                parse_mode="HTML",
                disable_notification=True,
            )
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    await message.answer(
        f"📊 Рассылка завершена.\n✅ Отправлено: {sent}\n❌ Ошибок: {failed}"
    )
    await state.clear()


@router.callback_query(F.data == "admin_backup")
async def admin_backup(callback: CallbackQuery):
    import shutil
    from datetime import datetime
    from pathlib import Path

    user_id = callback.from_user.id
    if not is_admin(user_id):
        return

    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.telegram_id == user_id)
        )
        db_user = result.scalar_one_or_none()
        lang = db_user.language if db_user else "ru"

    try:
        src = Path("data") / "bot.db"
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = backup_dir / f"bot_backup_{timestamp}.db"
        if src.exists():
            shutil.copy2(src, dst)
        text = f"💾 Backup создан: {dst}"
    except Exception as e:
        text = f"❌ Ошибка: {e}"

    await safe_edit(callback,
        text,
        reply_markup=admin_panel_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_reset_db")
async def admin_reset_db_confirm(callback: CallbackQuery):
    user_id = callback.from_user.id
    if not is_admin(user_id):
        return
    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.telegram_id == user_id)
        )
        db_user = result.scalar_one_or_none()
        lang = db_user.language if db_user else "ru"

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, сбросить", callback_data="admin_reset_do")],
        [InlineKeyboardButton(text="❌ Нет", callback_data="admin_panel")],
    ])
    await safe_edit(callback,
        _("admin.reset_confirm", lang),
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_reset_do")
async def admin_reset_do(callback: CallbackQuery):
    user_id = callback.from_user.id
    if not is_admin(user_id):
        return
    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.telegram_id == user_id)
        )
        db_user = result.scalar_one_or_none()
        lang = db_user.language if db_user else "ru"

    await reset_database()
    await safe_edit(callback,
        _("admin.reset_done", lang),
        reply_markup=main_menu(lang, is_admin=True),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "support")
async def show_support(callback: CallbackQuery):
    user_id = callback.from_user.id
    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.telegram_id == user_id)
        )
        db_user = result.scalar_one_or_none()
        lang = db_user.language if db_user else "ru"

    await safe_edit(callback,
        _("support.title", lang) + "\n\n" + _("support.contact", lang),
        reply_markup=back_button(lang),
        parse_mode="HTML"
    )
    await callback.answer()
