from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    telegram_token: str
    payment_api_base_url: str
    payment_api_key: str
    ticket_price: int
    currency: str
    sqlite_path: str

    @staticmethod
    def from_env() -> "Settings":
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        payment_api_base_url = os.getenv("PAYMENT_API_BASE_URL", "")
        payment_api_key = os.getenv("PAYMENT_API_KEY", "")
        ticket_price = int(os.getenv("TICKET_PRICE", "500"))
        currency = os.getenv("TICKET_CURRENCY", "RUB")
        sqlite_path = os.getenv("SQLITE_PATH", "lottery.db")

        if not telegram_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        if not payment_api_base_url:
            raise ValueError("PAYMENT_API_BASE_URL is required")
        if not payment_api_key:
            raise ValueError("PAYMENT_API_KEY is required")

        return Settings(
            telegram_token=telegram_token,
            payment_api_base_url=payment_api_base_url.rstrip("/"),
            payment_api_key=payment_api_key,
            ticket_price=ticket_price,
            currency=currency,
            sqlite_path=sqlite_path,
        )
