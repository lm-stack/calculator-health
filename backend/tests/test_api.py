"""Tests for the FastAPI endpoints (requires Supabase connection)."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client. Requires valid Supabase credentials in .env."""
    from app.main import app
    return TestClient(app)


class TestHealthEndpoints:
    """Test basic health endpoints (no Supabase needed)."""

    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestEmployeeEndpoints:
    """Test employee CRUD (requires Supabase)."""

    @pytest.mark.skip(reason="Requires Supabase connection")
    def test_list_employees(self, client):
        response = client.get("/api/employees")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.skip(reason="Requires Supabase connection")
    def test_create_employee(self, client):
        response = client.post("/api/employees", json={
            "first_name": "Test",
            "last_name": "User",
            "role": "infirmier",
            "activity_rate": 100,
            "can_do_night": True,
            "can_do_weekend": True,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "Test"
        assert data["role"] == "infirmier"


class TestScheduleEndpoints:
    """Test schedule generation (requires Supabase + seed data)."""

    @pytest.mark.skip(reason="Requires Supabase connection with seed data")
    def test_generate_schedule(self, client):
        response = client.post("/api/schedules/generate", json={
            "period_start": "2026-03-02",
            "period_end": "2026-03-08",
        })
        assert response.status_code in (201, 422)  # 422 if no feasible solution
