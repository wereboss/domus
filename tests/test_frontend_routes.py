def test_serve_index_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Domus - Your Home, Organised" in response.text
    assert "alpine.min.js" in response.text
    assert "floating-fab" in response.text
    assert "Financials" in response.text

def test_serve_pwa_manifest(client):
    response = client.get("/manifest.json")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Domus - Your Home, Organised"
    assert data["display"] == "standalone"

def test_serve_service_worker(client):
    response = client.get("/sw.js")
    assert response.status_code == 200
    assert "CACHE_NAME" in response.text

def test_serve_static_assets(client):
    css_resp = client.get("/static/css/app.css")
    assert css_resp.status_code == 200
    assert "--bottom-bar-height" in css_resp.text

    pico_resp = client.get("/static/vendor/pico.min.css")
    assert pico_resp.status_code == 200

    icon_resp = client.get("/static/icons/icon.svg")
    assert icon_resp.status_code == 200
