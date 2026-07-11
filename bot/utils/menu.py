from pathlib import Path
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardMarkup

_MENU_IMAGE = Path(__file__).resolve().parent.parent.parent / "assets" / "menu.jpg"


def has_menu_image() -> bool:
    return _MENU_IMAGE.exists()


async def send_menu(
    target: Message | CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup,
    parse_mode: str = "HTML"
):
    msg = target.message if isinstance(target, CallbackQuery) else target
    if has_menu_image():
        photo = FSInputFile(str(_MENU_IMAGE))
        await msg.answer_photo(
            photo=photo, caption=text,
            reply_markup=reply_markup, parse_mode=parse_mode,
        )
    else:
        await msg.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)


async def safe_edit(
    target: CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    parse_mode: str = "HTML",
    **kwargs,
):
    msg = target.message
    if msg.caption is not None:
        await msg.edit_caption(caption=text, reply_markup=reply_markup, parse_mode=parse_mode, **kwargs)
    else:
        await msg.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode, **kwargs)
