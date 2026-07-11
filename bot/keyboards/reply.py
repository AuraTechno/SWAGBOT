from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from bot.utils.i18n import _


def channel_subscribe_keyboard(channel_url: str, lang: str = "ru") -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="📢 " + (_("channel.check", lang)))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)
