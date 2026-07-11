from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from datetime import datetime, timezone
from sqlalchemy import select
from bot.database.db import async_session
from bot.database.models import User as UserModel, Admin as AdminModel
from bot.keyboards.inline import language_keyboard, main_menu
from bot.utils.i18n import _
from bot.utils.helpers import generate_referral_code
from bot.utils.menu import send_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    args = message.text.split()

    ref_code = None
    if len(args) > 1 and args[1].startswith("ref_"):
        ref_code = args[1][4:]

    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.telegram_id == user.id)
        )
        db_user = result.scalar_one_or_none()

        if db_user is None:
            db_user = UserModel(
                telegram_id=user.id,
                username=user.username,
                referral_code=generate_referral_code(),
            )
            session.add(db_user)
            await session.commit()
            await session.refresh(db_user)

            if ref_code:
                ref_result = await session.execute(
                    select(UserModel).where(UserModel.referral_code == ref_code)
                )
                referrer = ref_result.scalar_one_or_none()
                if referrer and referrer.telegram_id != user.id:
                    db_user.referred_by_id = referrer.telegram_id
                    await session.commit()

    await message.answer(
        _("start.welcome", db_user.language),
        reply_markup=language_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("lang_"))
async def set_language(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    user_id = callback.from_user.id

    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.telegram_id == user_id)
        )
        db_user = result.scalar_one_or_none()
        if db_user:
            db_user.language = lang
            await session.commit()

        admin = await session.execute(
            select(AdminModel).where(AdminModel.telegram_id == user_id)
        )
        is_admin = admin.scalar_one_or_none() is not None

    await safe_edit(
        callback,
        _("start.main_menu", lang, telegram_id=user_id),
        main_menu(lang, is_admin),
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    user_id = callback.from_user.id

    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.telegram_id == user_id)
        )
        db_user = result.scalar_one_or_none()
        lang = db_user.language if db_user else "ru"

        admin = await session.execute(
            select(AdminModel).where(AdminModel.telegram_id == user_id)
        )
        is_admin = admin.scalar_one_or_none() is not None

    await safe_edit(
        callback,
        _("start.main_menu", lang, telegram_id=user_id),
        main_menu(lang, is_admin),
    )
    await callback.answer()


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    user = message.from_user
    async with async_session() as session:
        result = await session.execute(
            select(UserModel).where(UserModel.telegram_id == user.id)
        )
        db_user = result.scalar_one_or_none()
        lang = db_user.language if db_user else "ru"

        is_admin = False
        admin_result = await session.execute(
            select(AdminModel).where(AdminModel.telegram_id == user.id)
        )
        is_admin = admin_result.scalar_one_or_none() is not None

    await send_menu(
        message,
        _("start.main_menu", lang, telegram_id=user.id),
        main_menu(lang, is_admin),
    )
