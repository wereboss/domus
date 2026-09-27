import io
from pathlib import Path
from app.models.inbox import UnprocessedInbox
from app.models.logistics import Task, Note
from app.models.finance import LedgerExpense

def test_share_target_get_link(client, logistics_session):
    resp = client.get("/share-target?title=Easy%20Pasta&url=https://cooking.nytimes.com/pasta")
    assert resp.status_code == 200
    assert "Saved to Family Inbox" in resp.text

    # Verify saved in unprocessed_inbox
    item = logistics_session.query(UnprocessedInbox).filter(
        UnprocessedInbox.raw_content == "https://cooking.nytimes.com/pasta"
    ).first()
    assert item is not None
    assert item.item_type == "link"
    assert item.status == "pending"
    assert item.source == "share_target"

def test_share_target_post_text(client, logistics_session):
    resp = client.post("/share-target", data={
        "text": "Call school nurse regarding asthma inhaler"
    })
    assert resp.status_code == 200
    assert "Saved to Family Inbox" in resp.text

    item = logistics_session.query(UnprocessedInbox).filter(
        UnprocessedInbox.raw_content.contains("asthma inhaler")
    ).first()
    assert item is not None
    assert item.item_type == "text"
    assert item.status == "pending"

def test_share_target_post_image_upload(client, logistics_session):
    file_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIFfakeimagecontent"
    resp = client.post(
        "/share-target",
        data={"title": "Supermarket Receipt"},
        files={"files": ("receipt.jpg", file_bytes, "image/jpeg")}
    )
    assert resp.status_code == 200
    assert "Saved to Family Inbox" in resp.text

    item = logistics_session.query(UnprocessedInbox).filter(
        UnprocessedInbox.file_name == "receipt.jpg"
    ).first()
    assert item is not None
    assert item.item_type == "image"
    assert item.file_path is not None
    assert item.status == "pending"

def test_share_target_rejects_unsupported_extension(client):
    file_bytes = b"echo 'harmful script'"
    resp = client.post(
        "/share-target",
        files={"files": ("exploit.sh", file_bytes, "application/x-sh")}
    )
    assert resp.status_code == 400
    assert "Unsupported file format" in resp.json()["detail"]

def test_inbox_api_crud_and_count(client):
    # Get initial count
    count_resp = client.get("/api/inbox/count")
    assert count_resp.status_code == 200
    initial_count = count_resp.json()["pending_count"]

    # In-app clipboard capture
    create_resp = client.post("/api/inbox", json={
        "title": "Amazon Order Tracking",
        "raw_content": "https://amazon.com/track/123",
        "source": "clipboard"
    })
    assert create_resp.status_code == 201
    item = create_resp.json()
    assert item["item_type"] == "link"
    item_id = item["id"]

    # Verify count incremented
    new_count_resp = client.get("/api/inbox/count")
    assert new_count_resp.json()["pending_count"] == initial_count + 1

    # Verify listing includes it
    list_resp = client.get("/api/inbox")
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert any(i["id"] == item_id for i in items)

def test_triage_inbox_to_task(client, logistics_session):
    create_resp = client.post("/api/inbox", json={
        "title": "Schedule dentist checkup",
        "raw_content": "Kids need 6-month cleaning",
        "source": "in_app_paste"
    })
    item_id = create_resp.json()["id"]

    # Triage convert to Task
    triage_payload = {
        "target_type": "task",
        "title": "Dentist cleaning for kids",
        "due_date": "2026-09-30",
        "due_time": "11:00",
        "priority": "urgent"
    }
    triage_resp = client.post(f"/api/inbox/{item_id}/triage", json=triage_payload)
    assert triage_resp.status_code == 200

    # Verify item status updated to processed
    inbox_item = logistics_session.query(UnprocessedInbox).filter(UnprocessedInbox.id == item_id).first()
    assert inbox_item.status == "processed"

    # Verify task created
    task = logistics_session.query(Task).filter(Task.title == "Dentist cleaning for kids").first()
    assert task is not None
    assert task.due_date == "2026-09-30"
    assert task.priority == "urgent"

def test_triage_inbox_to_expense(client, logistics_session, finance_session):
    create_resp = client.post("/api/inbox", json={
        "title": "Target receipt",
        "raw_content": "Target receipt: $64.80 for school supplies",
        "source": "in_app_paste"
    })
    item_id = create_resp.json()["id"]

    # Triage convert to Expense
    triage_payload = {
        "target_type": "expense",
        "title": "Target - School Supplies",
        "amount": 64.80,
        "category": "Kids",
        "payment_method": "Card"
    }
    triage_resp = client.post(f"/api/inbox/{item_id}/triage", json=triage_payload)
    assert triage_resp.status_code == 200

    # Verify inbox item processed
    inbox_item = logistics_session.query(UnprocessedInbox).filter(UnprocessedInbox.id == item_id).first()
    assert inbox_item.status == "processed"

    # Verify expense created in finance.db
    expense = finance_session.query(LedgerExpense).filter(LedgerExpense.title == "Target - School Supplies").first()
    assert expense is not None
    assert expense.amount == 64.80
    assert expense.category == "Kids"

def test_triage_inbox_to_note(client, logistics_session):
    create_resp = client.post("/api/inbox", json={
        "title": "Emergency Plumber Contact",
        "raw_content": "Joe's Plumbing: 555-0199",
        "source": "clipboard"
    })
    item_id = create_resp.json()["id"]

    # Triage convert to Note
    triage_payload = {
        "target_type": "note",
        "title": "Joe's Plumbing Hotline",
        "content": "555-0199 / 24h emergency leak repair"
    }
    triage_resp = client.post(f"/api/inbox/{item_id}/triage", json=triage_payload)
    assert triage_resp.status_code == 200

    note = logistics_session.query(Note).filter(Note.title == "Joe's Plumbing Hotline").first()
    assert note is not None
    assert "555-0199" in note.content

def test_dismiss_inbox_item(client, logistics_session):
    create_resp = client.post("/api/inbox", json={
        "title": "Unwanted spam link",
        "raw_content": "https://spam.test/ad",
        "source": "clipboard"
    })
    item_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/inbox/{item_id}")
    assert del_resp.status_code == 204

    inbox_item = logistics_session.query(UnprocessedInbox).filter(UnprocessedInbox.id == item_id).first()
    assert inbox_item.status == "dismissed"
