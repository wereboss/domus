def test_create_expense_and_bill(client):
    # Create ledger expense
    expense_data = {
        "title": "Trader Joe's Groceries",
        "amount": 84.50,
        "category": "Groceries",
        "date": "2026-09-27",
        "payment_method": "Card"
    }
    exp_resp = client.post("/api/expenses", json=expense_data)
    assert exp_resp.status_code == 201
    assert exp_resp.json()["amount"] == 84.50

    # Create fixed bill
    bill_data = {
        "title": "Fiber Internet Gigabit",
        "amount": 70.00,
        "category": "Utilities",
        "recurrence": "monthly",
        "due_day_of_month": 27,
        "is_auto_pay": True
    }
    bill_resp = client.post("/api/bills", json=bill_data)
    assert bill_resp.status_code == 201
    assert bill_resp.json()["due_day_of_month"] == 27
