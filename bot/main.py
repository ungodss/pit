from __future__ import annotations

import logging

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from bot.config import Settings
from bot.payment_client import PaymentApiClient
from bot.storage import LotteryStorage

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


START_TEXT = (
    "Привет! Я бот для розыгрыша лотереи.\n\n"
    "1) Нажмите «Купить билет».\n"
    "2) Оплатите по реквизитам.\n"
    "3) Нажмите «Проверить оплату».\n"
    "После подтверждения оплаты я выдам номер для участия в розыгрыше."
)


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎟 Купить билет", callback_data="buy_ticket")],
            [InlineKeyboardButton("✅ Проверить оплату", callback_data="check_payment")],
        ]
    )


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_message:
        return
    await update.effective_message.reply_text(START_TEXT, reply_markup=main_menu())


async def buy_ticket_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not update.effective_user:
        return

    await query.answer()

    settings: Settings = context.application.bot_data["settings"]
    payment_client: PaymentApiClient = context.application.bot_data["payment_client"]
    storage: LotteryStorage = context.application.bot_data["storage"]

    try:
        payment = await payment_client.create_payment(
            amount=settings.ticket_price,
            currency=settings.currency,
            telegram_user_id=update.effective_user.id,
        )
    except Exception as exc:
        logger.exception("Failed to create payment", exc_info=exc)
        await query.edit_message_text(
            "Не удалось создать оплату. Попробуйте позже.", reply_markup=main_menu()
        )
        return

    storage.create_purchase(
        telegram_user_id=update.effective_user.id,
        telegram_username=update.effective_user.username or "unknown",
        payment_id=payment.payment_id,
        amount=settings.ticket_price,
    )

    lines = [
        "Оплата создана.",
        f"Сумма: {settings.ticket_price} {settings.currency}",
        f"ID платежа: {payment.payment_id}",
    ]
    if payment.requisites:
        lines.append(f"Реквизиты: {payment.requisites}")
    if payment.payment_url:
        lines.append(f"Ссылка для оплаты: {payment.payment_url}")

    lines.append("\nПосле оплаты нажмите «Проверить оплату».")
    await query.edit_message_text("\n".join(lines), reply_markup=main_menu())


async def check_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not update.effective_user:
        return

    await query.answer()

    payment_client: PaymentApiClient = context.application.bot_data["payment_client"]
    storage: LotteryStorage = context.application.bot_data["storage"]

    latest_purchase = storage.get_latest_purchase_for_user(update.effective_user.id)

    if not latest_purchase:
        await query.edit_message_text(
            "У вас пока нет созданных платежей. Нажмите «Купить билет».",
            reply_markup=main_menu(),
        )
        return

    payment_id = latest_purchase.payment_id

    try:
        payment_info = await payment_client.get_payment(payment_id)
    except Exception as exc:
        logger.exception("Failed to check payment", exc_info=exc)
        await query.edit_message_text(
            "Не удалось проверить оплату. Попробуйте позже.",
            reply_markup=main_menu(),
        )
        return

    if payment_info.status.lower() != "paid":
        await query.edit_message_text(
            f"Оплата еще не подтверждена (статус: {payment_info.status}).",
            reply_markup=main_menu(),
        )
        return

    ticket_number = storage.mark_as_paid_and_assign_ticket(payment_id)
    await query.edit_message_text(
        (
            "✅ Оплата подтверждена!\n"
            f"Ваш номер для розыгрыша: #{ticket_number}\n"
            "Сохраните этот номер до объявления результатов."
        ),
        reply_markup=main_menu(),
    )


async def shutdown_handler(app: Application) -> None:
    payment_client: PaymentApiClient = app.bot_data["payment_client"]
    await payment_client.close()


def run() -> None:
    load_dotenv()
    settings = Settings.from_env()

    application = Application.builder().token(settings.telegram_token).build()
    application.bot_data["settings"] = settings
    application.bot_data["payment_client"] = PaymentApiClient(
        base_url=settings.payment_api_base_url,
        api_key=settings.payment_api_key,
    )
    application.bot_data["storage"] = LotteryStorage(settings.sqlite_path)

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CallbackQueryHandler(buy_ticket_handler, pattern="^buy_ticket$"))
    application.add_handler(
        CallbackQueryHandler(check_payment_handler, pattern="^check_payment$")
    )

    application.post_shutdown = shutdown_handler
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run()
