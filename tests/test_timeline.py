def test_unified_timeline_aggregation(client):
    target_date = "2026-09-27"

    # Add a task due at 14:00
    client.post("/api/tasks", json={
        "title": "Dentist appointment",
        "due_date": target_date,
        "due_time": "14:00",
        "priority": "normal"
    })

    # Add an overdue task from yesterday
    client.post("/api/tasks", json={
        "title": "Submit school permission slip",
        "due_date": "2026-09-26",
        "priority": "urgent"
    })

    # Add a bill due on the 27th
    client.post("/api/bills", json={
        "title": "Electricity Bill",
        "amount": 125.00,
        "category": "Utilities",
        "recurrence": "monthly",
        "due_day_of_month": 27,
        "is_auto_pay": False
    })

    # Add an expense on target date
    client.post("/api/expenses", json={
        "title": "School lunch recharge",
        "amount": 30.00,
        "category": "Kids",
        "date": target_date,
        "payment_method": "Card"
    })

    # Fetch unified timeline
    response = client.get(f"/api/timeline?date={target_date}")
    assert response.status_code == 200
    timeline = response.json()
    assert timeline["date"] == target_date
    
    summary = timeline["summary"]
    assert summary["total_due_bills_amount"] >= 125.00
    assert summary["total_spent_today"] >= 30.00

    items = timeline["items"]
    # Check that overdue task is present and marked overdue
    overdue_items = [i for i in items if i["is_overdue"]]
    assert len(overdue_items) >= 1
    assert any("permission slip" in i["title"] for i in overdue_items)

    # Check that bill is present
    bill_items = [i for i in items if i["item_type"] == "bill"]
    assert any("Electricity Bill" in i["title"] for i in bill_items)
