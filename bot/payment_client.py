from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class PaymentInfo:
    payment_id: str
    status: str
    payment_url: str | None
    requisites: str | None


class PaymentApiClient:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=15.0,
            headers={"Authorization": f"Bearer {api_key}"},
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def create_payment(
        self,
        amount: int,
        currency: str,
        telegram_user_id: int,
    ) -> PaymentInfo:
        payload = {
            "amount": amount,
            "currency": currency,
            "metadata": {"telegram_user_id": str(telegram_user_id)},
        }
        response = await self._client.post("/payments", json=payload)
        response.raise_for_status()
        data = response.json()
        return self._to_payment_info(data)

    async def get_payment(self, payment_id: str) -> PaymentInfo:
        response = await self._client.get(f"/payments/{payment_id}")
        response.raise_for_status()
        data = response.json()
        return self._to_payment_info(data)

    @staticmethod
    def _to_payment_info(data: dict[str, Any]) -> PaymentInfo:
        return PaymentInfo(
            payment_id=str(data["payment_id"]),
            status=str(data.get("status", "pending")),
            payment_url=data.get("payment_url"),
            requisites=data.get("requisites"),
        )
