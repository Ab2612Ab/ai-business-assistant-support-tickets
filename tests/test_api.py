from fastapi.testclient import TestClient
from api.index import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_create_ticket_and_get():
    payload = {
        "customer_name": "Jane Doe",
        "customer_email": "jane@example.com",
        "subject": "Website is broken",
        "description": "The checkout page is not working.",
        "channel": "web"
    }
    created = client.post("/tickets", json=payload)
    assert created.status_code == 201
    ticket_id = created.json()["id"]
    assert created.json()["priority"] == "high"

    fetched = client.get(f"/tickets/{ticket_id}")
    assert fetched.status_code == 200
    assert len(fetched.json()["messages"]) == 1

def test_ai_assistant():
    response = client.post("/assistant", json={"message": "I cannot login to my account"})
    assert response.status_code == 200
    assert response.json()["intent"] == "account_support"
    assert response.json()["suggested_tags"] == ["account"]

def test_dashboard():
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "total_tickets" in response.json()
