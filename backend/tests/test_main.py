def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to BondGuard Pro API"}

def test_read_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_read_status(client):
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "environment" in data
    assert "version" in data
    assert "timestamp" in data

def test_read_database_status(client):
    response = client.get("/api/v1/system/database")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "connected"
    assert "timestamp" in data

def test_404(client):
    response = client.get("/nonexistent")
    assert response.status_code == 404
