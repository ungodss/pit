from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Optional


@dataclass
class Purchase:
    id: int
    telegram_user_id: int
    telegram_username: str
    payment_id: str
    amount: int
    status: str
    ticket_number: Optional[int]


class LotteryStorage:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS purchases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_user_id INTEGER NOT NULL,
                    telegram_username TEXT NOT NULL,
                    payment_id TEXT UNIQUE NOT NULL,
                    amount INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    ticket_number INTEGER UNIQUE,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def create_purchase(
        self,
        telegram_user_id: int,
        telegram_username: str,
        payment_id: str,
        amount: int,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO purchases (telegram_user_id, telegram_username, payment_id, amount)
                VALUES (?, ?, ?, ?)
                """,
                (telegram_user_id, telegram_username, payment_id, amount),
            )
            conn.commit()

    def find_purchase_by_payment_id(self, payment_id: str) -> Optional[Purchase]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM purchases WHERE payment_id = ?",
                (payment_id,),
            ).fetchone()
        return Purchase(**dict(row)) if row else None


    def get_latest_purchase_for_user(self, telegram_user_id: int) -> Optional[Purchase]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM purchases
                WHERE telegram_user_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (telegram_user_id,),
            ).fetchone()
        return Purchase(**dict(row)) if row else None
    def mark_as_paid_and_assign_ticket(self, payment_id: str) -> Optional[int]:
        with self._connect() as conn:
            current_row = conn.execute(
                "SELECT status, ticket_number FROM purchases WHERE payment_id = ?",
                (payment_id,),
            ).fetchone()
            if not current_row:
                return None

            if current_row["status"] == "paid" and current_row["ticket_number"] is not None:
                return int(current_row["ticket_number"])

            max_ticket_row = conn.execute(
                "SELECT COALESCE(MAX(ticket_number), 0) AS last_ticket FROM purchases"
            ).fetchone()
            next_ticket = int(max_ticket_row["last_ticket"]) + 1

            conn.execute(
                """
                UPDATE purchases
                SET status = 'paid',
                    ticket_number = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE payment_id = ?
                """,
                (next_ticket, payment_id),
            )
            conn.commit()
            return next_ticket
