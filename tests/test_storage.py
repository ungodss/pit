from bot.storage import LotteryStorage


def test_assigns_incremental_ticket_numbers(tmp_path):
    db_path = tmp_path / "lottery.db"
    storage = LotteryStorage(str(db_path))

    storage.create_purchase(1, "user1", "pay_1", 500)
    storage.create_purchase(2, "user2", "pay_2", 500)

    first = storage.mark_as_paid_and_assign_ticket("pay_1")
    second = storage.mark_as_paid_and_assign_ticket("pay_2")

    assert first == 1
    assert second == 2


def test_reuses_existing_ticket_for_paid_payment(tmp_path):
    db_path = tmp_path / "lottery.db"
    storage = LotteryStorage(str(db_path))

    storage.create_purchase(1, "user1", "pay_1", 500)
    first = storage.mark_as_paid_and_assign_ticket("pay_1")
    second = storage.mark_as_paid_and_assign_ticket("pay_1")

    assert first == 1
    assert second == 1
