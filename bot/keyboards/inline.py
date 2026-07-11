from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.utils.i18n import _


def language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🇷🇺 Русский", callback_data="lang_ru")
    builder.button(text="🇬🇧 English", callback_data="lang_en")
    builder.adjust(2)
    return builder.as_markup()


def main_menu(lang: str = "ru", is_admin: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=_("buttons.profile", lang), callback_data="profile")
    builder.button(text=_("buttons.my_subscriptions", lang), callback_data="my_subs")
    builder.button(text=_("buttons.subscribe", lang), callback_data="subscribe")
    builder.button(text=_("buttons.trial", lang), callback_data="trial")
    builder.button(text=_("buttons.referral", lang), callback_data="referral")
    builder.button(text=_("buttons.gift", lang), callback_data="gift")
    builder.button(text=_("buttons.support", lang), callback_data="support")
    if is_admin:
        builder.button(text=_("buttons.admin_panel", lang), callback_data="admin_panel")
    builder.adjust(2)
    return builder.as_markup()


def sub_duration_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for months in [1, 3, 6, 12]:
        label = f"{months} {'мес.' if lang == 'ru' else 'mo.'}"
        builder.button(text=label, callback_data=f"sub_dur_{months}")
    builder.button(text=_("buttons.back", lang), callback_data="back_to_menu")
    builder.adjust(2)
    return builder.as_markup()


def sub_users_keyboard(months: int, lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for count in range(1, 5):
        builder.button(
            text=_("subscribe.users_count", lang, count=count),
            callback_data=f"sub_users_{months}_{count}"
        )
    builder.button(text=_("buttons.back", lang), callback_data="subscribe")
    builder.adjust(2)
    return builder.as_markup()


def confirm_keyboard(months: int, users: int, lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=_("buttons.confirm", lang), callback_data=f"sub_confirm_{months}_{users}")
    builder.button(text=_("buttons.cancel", lang), callback_data="back_to_menu")
    builder.adjust(2)
    return builder.as_markup()


def payment_keyboard(pay_url: str, lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=_("subscribe.pay", lang, amount=""), url=pay_url)
    builder.button(text=_("buttons.back_to_menu", lang), callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


def trial_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=_("trial.activate", lang), callback_data="activate_trial")
    builder.button(text=_("buttons.back", lang), callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_panel_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=_("admin.stats", lang), callback_data="admin_stats")
    builder.button(text=_("admin.create_gift", lang), callback_data="admin_create_gift")
    builder.button(text=_("admin.mailing", lang), callback_data="admin_mailing")
    builder.button(text=_("admin.backup", lang), callback_data="admin_backup")
    builder.button(text=_("admin.reset_db", lang), callback_data="admin_reset_db")
    builder.button(text=_("buttons.back_to_menu", lang), callback_data="back_to_menu")
    builder.adjust(2)
    return builder.as_markup()


def subs_list_keyboard(subs: list, lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for sub in subs:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        end = sub.end_date.replace(tzinfo=None) if sub.end_date.tzinfo else sub.end_date
        if not sub.is_active or end <= now:
            icon = "🔴"
        elif (end - now).days <= 7:
            icon = "🟡"
        else:
            icon = "🟢"
        label = f"{icon} #{sub.id} — {sub.type} ({sub.duration_months}мес)"
        builder.button(text=label, callback_data=f"sub_detail_{sub.id}")
    builder.button(text=_("buttons.back", lang), callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


def sub_detail_keyboard(sub_id: int, sub_url: str | None, lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if sub_url:
        builder.button(text=_("subscriptions.connect", lang), url=sub_url)
    builder.button(text=_("buttons.back", lang), callback_data="my_subs")
    builder.adjust(1)
    return builder.as_markup()


def back_button(lang: str = "ru") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=_("buttons.back", lang), callback_data="back_to_menu")
    return builder.as_markup()
