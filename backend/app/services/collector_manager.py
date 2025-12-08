"""Collector manager for managing all data collectors."""

import asyncio
import logging

from sqlalchemy import select

from app.collectors.base import BaseCollector
from app.collectors.meshmonitor import MeshMonitorCollector
from app.collectors.mqtt import MqttCollector
from app.database import async_session_maker
from app.models import Source
from app.models.source import SourceType

logger = logging.getLogger(__name__)


class CollectorManager:
    """Manages all data collectors."""

    def __init__(self):
        self._collectors: dict[str, BaseCollector] = {}
        self._running = False

    async def start(self) -> None:
        """Start all enabled collectors."""
        if self._running:
            return

        self._running = True
        await self._load_collectors()
        logger.info(f"Started {len(self._collectors)} collectors")

    async def _load_collectors(self) -> None:
        """Load and start collectors for all enabled sources."""
        async with async_session_maker() as db:
            result = await db.execute(
                select(Source).where(Source.enabled == True)  # noqa: E712
            )
            sources = result.scalars().all()

            for source in sources:
                await self._start_collector(source)

    async def _start_collector(self, source: Source) -> None:
        """Start a collector for a source."""
        if source.id in self._collectors:
            return

        if source.type == SourceType.MESHMONITOR:
            collector = MeshMonitorCollector(source)
        elif source.type == SourceType.MQTT:
            collector = MqttCollector(source)
        else:
            logger.warning(f"Unknown source type: {source.type}")
            return

        self._collectors[source.id] = collector
        await collector.start()

    async def stop(self) -> None:
        """Stop all collectors."""
        self._running = False

        # Stop all collectors concurrently
        await asyncio.gather(
            *[collector.stop() for collector in self._collectors.values()],
            return_exceptions=True,
        )

        self._collectors.clear()
        logger.info("Stopped all collectors")

    async def add_source(self, source: Source) -> None:
        """Add and start a collector for a new source."""
        if source.enabled:
            await self._start_collector(source)

    async def remove_source(self, source_id: str) -> None:
        """Stop and remove a collector."""
        collector = self._collectors.pop(source_id, None)
        if collector:
            await collector.stop()

    async def update_source(self, source: Source) -> None:
        """Update a collector when source config changes."""
        # Stop existing collector
        await self.remove_source(source.id)

        # Start new one if enabled
        if source.enabled:
            await self._start_collector(source)

    def get_collector(self, source_id: str) -> BaseCollector | None:
        """Get a collector by source ID."""
        return self._collectors.get(source_id)


# Global collector manager instance
collector_manager = CollectorManager()
