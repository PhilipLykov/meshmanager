#!/usr/bin/env python3
"""Trigger historical data collection for all MeshMonitor sources.

This script must be run from within the backend container or with
the correct Python path set up.

Usage:
    docker exec meshmanager-backend-dev python scripts/trigger_historical.py
"""

import asyncio
import sys

# Add the app to path
sys.path.insert(0, "/app")

from app.collectors.meshmonitor import MeshMonitorCollector
from app.database import async_session_maker
from app.models import Source
from app.models.source import SourceType
from sqlalchemy import select


async def main():
    print("Fetching MeshMonitor sources...")

    async with async_session_maker() as db:
        result = await db.execute(
            select(Source).where(
                Source.enabled == True,  # noqa: E712
                Source.type == SourceType.MESHMONITOR,
            )
        )
        sources = result.scalars().all()

    if not sources:
        print("No enabled MeshMonitor sources found.")
        return

    print(f"Found {len(sources)} MeshMonitor source(s)")

    for source in sources:
        print(f"\nStarting historical collection for: {source.name}")
        print(f"  URL: {source.url}")

        collector = MeshMonitorCollector(source)
        # Set _running to True so the collection loop doesn't exit immediately
        collector._running = True

        # Run historical collection
        await collector.collect_historical_batch(
            batch_size=500,
            delay_seconds=5.0,  # 5 second delay between batches
            max_batches=100,    # Up to 50,000 records
        )

        print(f"Historical collection complete for: {source.name}")
        print(f"  Status: {collector.collection_status.status}")
        print(f"  Total collected: {collector.collection_status.total_collected}")
        if collector.collection_status.last_error:
            print(f"  Last error: {collector.collection_status.last_error}")


if __name__ == "__main__":
    asyncio.run(main())
