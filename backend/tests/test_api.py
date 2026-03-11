"""Integration tests for CareAgent OS API endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestRootEndpoints:
    @pytest.mark.asyncio
    async def test_root(self, client):
        r = await client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "CareAgent OS"
        assert len(data["agents"]) == 6

    @pytest.mark.asyncio
    async def test_health(self, client):
        r = await client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"


class TestSystemEndpoints:
    @pytest.mark.asyncio
    async def test_status(self, client):
        r = await client.get("/api/status")
        assert r.status_code == 200
        data = r.json()
        assert data["app"] == "CareAgent OS"
        assert "system" in data

    @pytest.mark.asyncio
    async def test_agents_list(self, client):
        r = await client.get("/api/agents")
        assert r.status_code == 200
        assert r.json()["total"] == 6

    @pytest.mark.asyncio
    async def test_activity_feed(self, client):
        r = await client.get("/api/activity-feed?limit=10")
        assert r.status_code == 200
        assert "activities" in r.json()


class TestOperationsEndpoints:
    @pytest.mark.asyncio
    async def test_dashboard(self, client):
        r = await client.get("/api/operations/dashboard")
        assert r.status_code == 200
        assert "metrics" in r.json()

    @pytest.mark.asyncio
    async def test_predictions(self, client):
        r = await client.get("/api/operations/predictions?days=3")
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_capacity(self, client):
        r = await client.get("/api/operations/capacity")
        assert r.status_code == 200


class TestTriageEndpoints:
    @pytest.mark.asyncio
    async def test_triage(self, client):
        r = await client.post("/api/triage", json={
            "symptoms": "headache and mild fever",
            "vital_signs": {},
            "patient_age": 30,
        })
        assert r.status_code == 200
        assert "triage" in r.json()


class TestDocumentationEndpoints:
    @pytest.mark.asyncio
    async def test_soap(self, client):
        r = await client.post("/api/documentation/soap", json={
            "symptoms": "cough for 3 days",
            "patient_age": 40,
        })
        assert r.status_code == 200
