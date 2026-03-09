def test_create_family(client):
    r = client.post("/api/families", json={"name": "Test Family", "chat_id": 111, "timezone": "UTC"})
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Test Family"
    assert data["chat_id"] == 111


def test_get_family_by_chat(client):
    client.post("/api/families", json={"name": "Test", "chat_id": 222})
    r = client.get("/api/families/222")
    assert r.status_code == 200
    assert r.json()["chat_id"] == 222


def test_get_family_not_found(client):
    r = client.get("/api/families/9999")
    assert r.status_code == 404


def test_duplicate_family(client):
    client.post("/api/families", json={"name": "A", "chat_id": 333})
    r = client.post("/api/families", json={"name": "B", "chat_id": 333})
    assert r.status_code == 409
