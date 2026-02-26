import httpx
import pytest

from bot.payment_client import PaymentApiClient


@pytest.mark.asyncio
async def test_create_payment_parses_response():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/payments"
        return httpx.Response(
            200,
            json={
                "payment_id": "pay_1",
                "status": "pending",
                "payment_url": "https://pay/1",
                "requisites": "card 1111",
            },
        )

    transport = httpx.MockTransport(handler)
    client = PaymentApiClient("https://example.com", "key")
    client._client = httpx.AsyncClient(
        base_url="https://example.com",
        headers={"Authorization": "Bearer key"},
        transport=transport,
    )

    payment = await client.create_payment(500, "RUB", 123)

    assert payment.payment_id == "pay_1"
    assert payment.status == "pending"
    assert payment.payment_url == "https://pay/1"
    assert payment.requisites == "card 1111"

    await client.close()
