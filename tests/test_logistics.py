def test_create_and_complete_task(client):
    profiles = client.get("/api/auth/profiles").json()
    mom = profiles[0]

    # Create task
    task_data = {
        "title": "Buy organic whole milk",
        "description": "2 gallons",
        "assigned_to_id": mom["id"],
        "due_date": "2026-09-27",
        "due_time": "10:30",
        "priority": "normal"
    }
    create_resp = client.post("/api/tasks", json=task_data)
    assert create_resp.status_code == 201
    task = create_resp.json()
    assert task["title"] == "Buy organic whole milk"
    assert task["is_completed"] is False
    assert task["assigned_to"]["name"] == mom["name"]

    # Toggle complete
    task_id = task["id"]
    patch_resp = client.patch(f"/api/tasks/{task_id}", json={"is_completed": True})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["is_completed"] is True
    assert patch_resp.json()["completed_at"] is not None

def test_chore_recurrence_advancement(client):
    chore_data = {
        "title": "Take out compost",
        "recurrence": "weekly",
        "next_due_date": "2026-09-27"
    }
    create_resp = client.post("/api/chores", json=chore_data)
    assert create_resp.status_code == 201
    chore = create_resp.json()
    chore_id = chore["id"]

    # Mark complete
    complete_resp = client.post(f"/api/chores/{chore_id}/complete")
    assert complete_resp.status_code == 200
    updated = complete_resp.json()
    assert updated["last_completed_at"] is not None
    assert updated["next_due_date"] > "2026-09-27"
