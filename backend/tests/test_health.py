"""Tests for health check endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    async def test_health_check_returns_200(self, client: AsyncClient):
        """Health check should return 200 status code."""
        response = await client.get("/health")
        assert response.status_code == 200

    async def test_health_check_response_structure(self, client: AsyncClient):
        """Health check should return expected JSON structure."""
        response = await client.get("/health")
        data = response.json()

        assert "status" in data
        assert "database" in data
        assert "version" in data

    async def test_health_check_status_field(self, client: AsyncClient):
        """Health check status should be 'healthy' or 'degraded'."""
        response = await client.get("/health")
        data = response.json()

        assert data["status"] in ["healthy", "degraded"]

    async def test_health_check_version_not_empty(self, client: AsyncClient):
        """Health check should return a non-empty version string."""
        response = await client.get("/health")
        data = response.json()

        assert data["version"]
        assert len(data["version"]) > 0

    async def test_health_check_database_status(self, client: AsyncClient):
        """Health check should report database status."""
        response = await client.get("/health")
        data = response.json()

        # With test DB, should be healthy
        assert data["database"] == "healthy"
