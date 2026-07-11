import stripe
import logging
from bot.config import config

logger = logging.getLogger(__name__)


async def create_stripe_payment(amount_rub: float, description: str) -> dict | None:
    if not config.STRIPE_API_KEY:
        logger.warning("Stripe API key not configured")
        return None
    try:
        stripe.api_key = config.STRIPE_API_KEY
        amount_cents = int(amount_rub * 100)
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": description},
                    "unit_amount": amount_cents,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url="https://t.me/...",
            cancel_url="https://t.me/...",
        )
        return {"url": session.url, "id": session.id}
    except Exception as e:
        logger.error(f"Stripe payment creation failed: {e}")
        return None


async def verify_stripe_payment(session_id: str) -> bool:
    try:
        stripe.api_key = config.STRIPE_API_KEY
        session = stripe.checkout.Session.retrieve(session_id)
        return session.payment_status == "paid"
    except Exception as e:
        logger.error(f"Stripe payment verification failed: {e}")
        return False
