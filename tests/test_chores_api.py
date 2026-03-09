import pytest


@pytest.fixture
def setup(client):
    fam = client.post("/api/families", json={"name": "Fam", "chat_id": 777}).json()
    m1 = client.post("/api/members", json={"family_id": fam["id"], "user_id": 1, "display_name": "A"}).json()
    m2 = client.post("/api/members", json={"family_id": fam["id"], "user_id": 2, "display_name": "B"}).json()
    return fam, m1, m2


def test_create_chore(client, setup):
    fam, m1, _ = setup
    r = client.post("/api/chores", json={
        "family_id": fam["id"],
        "title": "Wash dishes",
        "created_by": m1["id"],
    })
    assert r.status_code == 201
    assert r.json()["title"] == "Wash dishes"


def test_list_chores_filtered(client, setup):
    fam, m1, _ = setup
    client.post("/api/chores", json={"family_id": fam["id"], "title": "T1", "created_by": m1["id"]})
    client.post("/api/chores", json={"family_id": fam["id"], "title": "T2", "created_by": m1["id"]})
    r = client.get(f"/api/chores?family_id={fam['id']}&status=pending")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_assign_random(client, setup):
    fam, m1, m2 = setup
    chore = client.post("/api/chores", json={"family_id": fam["id"], "title": "Random", "created_by": m1["id"]}).json()
    r = client.post(f"/api/chores/{chore['id']}/assign", json={"mode": "random"})
    assert r.status_code == 200
    assert r.json()["assigned_to"] in [m1["id"], m2["id"]]


def test_complete_chore(client, setup):
    fam, m1, _ = setup
    chore = client.post("/api/chores", json={"family_id": fam["id"], "title": "Clean", "created_by": m1["id"]}).json()
    r = client.post(f"/api/chores/{chore['id']}/complete", json={"user_id": m1["id"]})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "completed"
    assert data["completed_at"] is not None


def test_history(client, setup):
    fam, m1, _ = setup
    chore = client.post("/api/chores", json={"family_id": fam["id"], "title": "History test", "created_by": m1["id"]}).json()
    client.post(f"/api/chores/{chore['id']}/complete", json={"user_id": m1["id"]})
    r = client.get(f"/api/chores/history?family_id={fam['id']}")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["status"] == "completed"
