from aiogram import Router, F
from aiogram.types import CallbackQuery
from datetime import datetime, timezone
from sqlalchemy import select
from bot.database.db import async_session
from bot.database.models import User as UserModel, Subscription
from bot.keyboards.inline import subs_list_keyboard, sub_detail_keyboard, back_button
from bot.utils.i18n import _
from bot.utils.menu import safe_edit
from bot.utils.helpers import format_date

router = Router()


@router.callback_query(F.data == "my_subs")
async def show_subscriptions(callback: CallbackQuery):
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

        subs_result = await session.execute(
            select(Subscription)
            .where(Subscription.user_id == db_user.id)
            .order_by(Subscription.end_date.desc())
        )
        subs = subs_result.scalars().all()

    if not subs:
        text = _("subscriptions.title", lang) + "\n\n" + _("subscriptions.empty", lang)
        await safe_edit(callback, text, reply_markup=back_button(lang))
        await callback.answer()
        return

    text = _("subscriptions.title", lang)
    await safe_edit(callback, text, reply_markup=subs_list_keyboard(subs, lang))
    await callback.answer()


@router.callback_query(F.data.startswith("sub_detail_"))
async def show_subscription_detail(callback: CallbackQuery):
    sub_id = int(callback.data.split("_")[2])
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

        sub_result = await session.execute(
            select(Subscription).where(
                Subscription.id == sub_id,
                Subscription.user_id == db_user.id,
            )
        )
        sub = sub_result.scalar_one_or_none()
        if not sub:
            await callback.answer(_("errors.unknown", lang), show_alert=True)
            return

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        end = sub.end_date.replace(tzinfo=None) if sub.end_date.tzinfo else sub.end_date
        if not sub.is_active or end <= now:
            status = _("subscriptions.status_expired", lang)
        elif (end - now).days <= 7:
            status = _("subscriptions.status_expiring", lang)
        elif sub.type == "trial":
            status = _("subscriptions.status_trial", lang)
        elif sub.type == "gift":
            status = _("subscriptions.status_gift", lang)
        else:
            status = _("subscriptions.status_active", lang)

        type_labels = {"paid": _("subscribe.payment_card", lang) if lang == "ru" else "Paid", "trial": _("buttons.trial", lang), "gift": _("buttons.gift", lang)}
        type_label = type_labels.get(sub.type, sub.type)

        text = _("subscriptions.detail_title", lang, id=sub.id) + "\n\n"
        text += _("subscriptions.detail_type", lang, type=type_label) + "\n"
        text += _("subscriptions.detail_duration", lang, months=sub.duration_months) + "\n"
        text += _("subscriptions.detail_users", lang, count=sub.users_count) + "\n"
        text += _("subscriptions.detail_start", lang, date=format_date(sub.start_date)) + "\n"
        text += _("subscriptions.detail_end", lang, date=format_date(sub.end_date)) + "\n"
        text += _("subscriptions.detail_status", lang, status=status)

        if sub.is_active and sub.end_date > now:
            text += "\n\n" + _("subscriptions.connect_info", lang)

    await safe_edit(
        callback, text,
        reply_markup=sub_detail_keyboard(sub.id, sub.subscription_url, lang),
    )
    await callback.answer()
