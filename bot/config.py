import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

    REQUIRED_CHANNEL_ID: str = os.getenv("REQUIRED_CHANNEL_ID", "")
    REQUIRED_CHANNEL_URL: str = os.getenv("REQUIRED_CHANNEL_URL", "")

    ADMIN_IDS: list[int] = [
        int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
    ]

    REMNAWAVE_BASE_URL: str = os.getenv("REMNAWAVE_BASE_URL", "")
    REMNAWAVE_TOKEN: str = os.getenv("REMNAWAVE_TOKEN", "")
    REMNAWAVE_NODE_UUID: str = os.getenv("REMNAWAVE_NODE_UUID", "")

    CRYPTO_BOT_TOKEN: str = os.getenv("CRYPTO_BOT_TOKEN", "")

    STRIPE_API_KEY: str = os.getenv("STRIPE_API_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/bot.db")

    NOTIFICATION_CHECK_INTERVAL_HOURS: int = int(
        os.getenv("NOTIFICATION_CHECK_INTERVAL_HOURS", "6")
    )

    TRIAL_DAYS: int = 3
    TRIAL_MAX_USERS: int = 1

    SUBSCRIPTION_OPTIONS = {
        1: {1: 299, 2: 499, 3: 699, 4: 899},
        3: {1: 699, 2: 1199, 3: 1699, 4: 2199},
        6: {1: 1199, 2: 1999, 3: 2899, 4: 3799},
        12: {1: 1999, 2: 3499, 3: 4999, 4: 6499},
    }

    REFERRAL_BONUS_DAYS: int = 7
    REFERRAL_BONUS_PERCENT: float = 10.0

    MAX_USERS_PER_SUBSCRIPTION: int = 4


config = Config()
