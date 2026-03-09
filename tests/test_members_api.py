def test_create_member(client):
    fam = client.post("/api/families", json={"name": "Fam", "chat_id": 444}).json()
    r = client.post("/api/members", json={
        "family_id": fam["id"],
        "user_id": 1001,
        "display_name": "Alice",
        "role": "admin",
    })
    assert r.status_code == 201
    assert r.json()["display_name"] == "Alice"


def test_list_members(client):
    fam = client.post("/api/families", json={"name": "Fam", "chat_id": 555}).json()
    client.post("/api/members", json={"family_id": fam["id"], "user_id": 1, "display_name": "A"})
    client.post("/api/members", json={"family_id": fam["id"], "user_id": 2, "display_name": "B"})
    r = client.get(f"/api/members?family_id={fam['id']}")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_get_member_by_user(client):
    fam = client.post("/api/families", json={"name": "Fam", "chat_id": 666}).json()
    client.post("/api/members", json={"family_id": fam["id"], "user_id": 999, "display_name": "Bob"})
    r = client.get(f"/api/members/by_user?user_id=999&family_id={fam['id']}")
    assert r.status_code == 200
    assert r.json()["user_id"] == 999


def test_patch_member_role(client):
    fam = client.post("/api/families", json={"name": "F", "chat_id": 777}).json()
    m = client.post("/api/members", json={"family_id": fam["id"], "user_id": 101, "display_name": "Alice", "role": "member"}).json()
    r = client.patch(f"/api/members/{m['id']}", json={"role": "admin"})
    assert r.status_code == 200
    assert r.json()["role"] == "admin"


def test_patch_member_not_found(client):
    r = client.patch("/api/members/99999", json={"role": "admin"})
    assert r.status_code == 404
