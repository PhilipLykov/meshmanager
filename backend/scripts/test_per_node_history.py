#!/usr/bin/env python3
"""Test per-node historical telemetry collection.

Usage:
    docker exec meshmanager-backend-dev python scripts/test_per_node_history.py
"""

import asyncio
import sys

sys.path.insert(0, "/app")

from app.collectors.meshmonitor import MeshMonitorCollector
from app.database import async_session_maker
from app.models import Source
from app.models.source import SourceType
from sqlalchemy import select


async def main():
    print("Fetching sentry.yeraze.online source...")

    async with async_session_maker() as db:
        result = await db.execute(
            select(Source).where(
                Source.enabled == True,  # noqa: E712
                Source.type == SourceType.MESHMONITOR,
                Source.url.contains("sentry"),
            )
        )
        source = result.scalar()

    if not source:
        print("No sentry.yeraze.online source found.")
        return

    print(f"Found source: {source.name}")
    print(f"  URL: {source.url}")

    collector = MeshMonitorCollector(source)
    collector._running = True

    # Test collecting history for a single node
    test_node_id = "!43588558"  # Yeraze Sandbox - has lots of data
    print(f"\nCollecting historical telemetry for node {test_node_id}...")

    total = await collector.collect_node_historical_telemetry(
        node_id=test_node_id,
        days_back=7,
        batch_size=500,
        delay_seconds=1.0,
        max_batches=10,  # Limit for testing
    )

    print(f"\nCollection complete!")
    print(f"  Total records collected: {total}")
    print(f"  Status: {collector.collection_status.to_dict()}")


if __name__ == "__main__":
    asyncio.run(main())
