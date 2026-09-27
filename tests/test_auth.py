def test_list_profiles(client):
    response = client.get("/api/auth/profiles")
    assert response.status_code == 200
    profiles = response.json()
    assert len(profiles) >= 2
    names = [p["name"] for p in profiles]
    assert "Mom" in names
    assert "Dad" in names

def test_login_success(client):
    profiles = client.get("/api/auth/profiles").json()
    mom = next(p for p in profiles if p["name"] == "Mom")
    
    # Correct PIN for Mom is 1234
    response = client.post("/api/auth/login", json={"member_id": mom["id"], "pin": "1234"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["member"]["name"] == "Mom"

    # Authenticated /me endpoint
    token = data["access_token"]
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["name"] == "Mom"

def test_login_incorrect_pin(client):
    profiles = client.get("/api/auth/profiles").json()
    mom = next(p for p in profiles if p["name"] == "Mom")
    
    response = client.post("/api/auth/login", json={"member_id": mom["id"], "pin": "9999"})
    assert response.status_code == 401
    assert "Incorrect PIN" in response.json()["detail"]
