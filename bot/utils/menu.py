from pathlib import Path
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

_MENU_IMAGE = Path(__file__).resolve().parent.parent.parent / "assets" / "menu.jpg"


def has_menu_image() -> bool:
    return _MENU_IMAGE.exists()


async def send_menu(
    target: Message | CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup,
    parse_mode: str = "HTML"
):
    if isinstance(target, CallbackQuery):
        target = target.message

    if has_menu_image():
        photo = FSInputFile(str(_MENU_IMAGE))
        await target.answer_photo(
            photo=photo,
            caption=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
    else:
        await target.answer(
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )


async def safe_edit_text(
    target: CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    parse_mode: str = "HTML"
):
    try:
        await target.message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        try:
            await target.message.delete()
        except Exception:
            pass
        await target.message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)


async def edit_or_send_menu(
    target: CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup,
    parse_mode: str = "HTML"
):
    if has_menu_image():
        try:
            await target.message.delete()
        except Exception:
            pass
        photo = FSInputFile(str(_MENU_IMAGE))
        await target.message.answer_photo(
            photo=photo,
            caption=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
    else:
        await target.message.edit_text(
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
