import random
import string
from datetime import datetime, timedelta, timezone


def generate_referral_code(length: int = 10) -> str:
    chars = string.ascii_letters + string.digits
    return "SWAG" + "".join(random.choices(chars, k=length))


def generate_gift_code() -> str:
    chars = string.ascii_uppercase + string.digits
    return "GIFT-" + "".join(random.choices(chars, k=12))


def format_date(dt: datetime) -> str:
    return dt.strftime("%d.%m.%Y %H:%M")


def calc_end_date(months: int) -> datetime:
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=30 * months)
    return end


def make_referral_link(code: str, bot_username: str) -> str:
    return f"https://t.me/{bot_username}?start=ref_{code}"
