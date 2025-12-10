"""Pytest configuration and fixtures."""

import os
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# Set testing environment before importing app modules
os.environ["TESTING"] = "true"


def pytest_configure(config):
    """Add custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (require PostgreSQL)"
    )


def pytest_collection_modifyitems(config, items):
    """Skip integration tests when running with SQLite (default)."""
    skip_integration = pytest.mark.skip(
        reason="Integration tests require PostgreSQL - run with TEST_DATABASE_URL env var"
    )
    for item in items:
        if "integration" in item.keywords:
            # Check if we have a PostgreSQL URL
            db_url = os.environ.get("TEST_DATABASE_URL", "")
            if not db_url.startswith("postgresql"):
                item.add_marker(skip_integration)


@pytest.fixture
def mock_db_session():
    """Create a mock database session for unit tests."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def sample_node_data():
    """Sample node data for testing."""
    return {
        "node_id": "!abc12345",
        "node_num": 12345678,
        "long_name": "Test Node",
        "short_name": "TST1",
        "latitude": 40.7128,
        "longitude": -74.006,
        "altitude": 10,
        "role": "2",
        "hw_model": "TBEAM",
    }


@pytest.fixture
def sample_source_data():
    """Sample source data for testing."""
    return {
        "name": "Test MeshMonitor",
        "source_type": "meshmonitor",
        "enabled": True,
        "url": "https://test.meshmonitor.example.com",
    }


@pytest.fixture
def sample_telemetry_data():
    """Sample telemetry data for testing."""
    return {
        "node_num": 12345678,
        "metric_name": "deviceMetrics",
        "battery_level": 85,
        "voltage": 4.1,
        "channel_utilization": 25.5,
        "air_util_tx": 5.2,
    }


# Integration test fixtures - only used when PostgreSQL is available
@pytest.fixture
async def test_engine():
    """Create a test database engine (requires PostgreSQL)."""
    from httpx import ASGITransport, AsyncClient
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.orm import sessionmaker

    from app.database import Base

    db_url = os.environ.get("TEST_DATABASE_URL", "")
    if not db_url:
        pytest.skip("TEST_DATABASE_URL not set")

    engine = create_async_engine(db_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine):
    """Create a test database session (requires PostgreSQL)."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker

    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest.fixture
async def client(test_session):
    """Create an async test client with test database (requires PostgreSQL)."""
    from httpx import ASGITransport, AsyncClient

    from app.database import get_db
    from app.main import app

    async def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()
