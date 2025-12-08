"""MeshMonitor API collector."""

import asyncio
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select

from app.collectors.base import BaseCollector
from app.database import async_session_maker
from app.models import Channel, Message, Node, Source, Telemetry, Traceroute
from app.schemas.source import SourceTestResult

logger = logging.getLogger(__name__)


class MeshMonitorCollector(BaseCollector):
    """Collector for MeshMonitor API sources."""

    def __init__(self, source: Source):
        super().__init__(source)
        self._running = False
        self._task: asyncio.Task | None = None

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for API requests."""
        headers = {"Accept": "application/json"}
        if self.source.api_token:
            headers["Authorization"] = f"Bearer {self.source.api_token}"
        return headers

    async def test_connection(self) -> SourceTestResult:
        """Test connection to the MeshMonitor API."""
        if not self.source.url:
            return SourceTestResult(success=False, message="No URL configured")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Try the health endpoint first
                response = await client.get(
                    f"{self.source.url}/api/health",
                    headers=self._get_headers(),
                )
                if response.status_code != 200:
                    return SourceTestResult(
                        success=False,
                        message=f"Health check failed: {response.status_code}",
                    )

                # Try to get nodes
                response = await client.get(
                    f"{self.source.url}/api/v1/network/nodes",
                    headers=self._get_headers(),
                )
                if response.status_code == 200:
                    data = response.json()
                    nodes = data if isinstance(data, list) else data.get("nodes", [])
                    return SourceTestResult(
                        success=True,
                        message="Connection successful",
                        nodes_found=len(nodes),
                    )
                else:
                    return SourceTestResult(
                        success=False,
                        message=f"Failed to fetch nodes: {response.status_code}",
                    )
        except httpx.TimeoutException:
            return SourceTestResult(success=False, message="Connection timeout")
        except httpx.RequestError as e:
            return SourceTestResult(success=False, message=f"Connection error: {e}")
        except Exception as e:
            return SourceTestResult(success=False, message=f"Error: {e}")

    async def collect(self) -> None:
        """Collect data from the MeshMonitor API."""
        if not self.source.url:
            logger.warning(f"Source {self.source.name} has no URL configured")
            return

        logger.info(f"Collecting from MeshMonitor: {self.source.name}")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = self._get_headers()

                # Collect nodes
                await self._collect_nodes(client, headers)

                # Collect messages
                await self._collect_messages(client, headers)

                # Collect telemetry
                await self._collect_telemetry(client, headers)

                # Collect traceroutes
                await self._collect_traceroutes(client, headers)

            # Update last poll time
            async with async_session_maker() as db:
                result = await db.execute(
                    select(Source).where(Source.id == self.source.id)
                )
                source = result.scalar()
                if source:
                    source.last_poll_at = datetime.now(timezone.utc)
                    source.last_error = None
                    await db.commit()

            logger.info(f"Collection complete for {self.source.name}")

        except Exception as e:
            logger.error(f"Collection error for {self.source.name}: {e}")
            # Record the error
            async with async_session_maker() as db:
                result = await db.execute(
                    select(Source).where(Source.id == self.source.id)
                )
                source = result.scalar()
                if source:
                    source.last_error = str(e)
                    await db.commit()

    async def _collect_nodes(self, client: httpx.AsyncClient, headers: dict) -> None:
        """Collect nodes from the API."""
        try:
            response = await client.get(
                f"{self.source.url}/api/v1/network/nodes",
                headers=headers,
            )
            if response.status_code != 200:
                logger.warning(f"Failed to fetch nodes: {response.status_code}")
                return

            data = response.json()
            nodes_data = data if isinstance(data, list) else data.get("nodes", [])

            async with async_session_maker() as db:
                for node_data in nodes_data:
                    await self._upsert_node(db, node_data)
                await db.commit()

            logger.debug(f"Collected {len(nodes_data)} nodes")
        except Exception as e:
            logger.error(f"Error collecting nodes: {e}")

    async def _upsert_node(self, db, node_data: dict) -> None:
        """Insert or update a node."""
        node_num = node_data.get("nodeNum") or node_data.get("num")
        if not node_num:
            return

        result = await db.execute(
            select(Node).where(
                Node.source_id == self.source.id,
                Node.node_num == node_num,
            )
        )
        node = result.scalar()

        position = node_data.get("position", {}) or {}

        if node:
            # Update existing node
            node.node_id = node_data.get("nodeId") or node_data.get("id")
            node.short_name = node_data.get("shortName")
            node.long_name = node_data.get("longName")
            node.hw_model = node_data.get("hwModel")
            node.role = node_data.get("role")
            node.latitude = position.get("latitude") or position.get("lat")
            node.longitude = position.get("longitude") or position.get("lon")
            node.altitude = position.get("altitude") or position.get("alt")
            if position.get("time"):
                node.position_time = datetime.fromtimestamp(
                    position["time"], tz=timezone.utc
                )
            node.position_precision_bits = position.get("precisionBits")
            if node_data.get("lastHeard"):
                node.last_heard = datetime.fromtimestamp(
                    node_data["lastHeard"], tz=timezone.utc
                )
            node.is_licensed = node_data.get("isLicensed", False)
            node.updated_at = datetime.now(timezone.utc)
        else:
            # Create new node
            node = Node(
                source_id=self.source.id,
                node_num=node_num,
                node_id=node_data.get("nodeId") or node_data.get("id"),
                short_name=node_data.get("shortName"),
                long_name=node_data.get("longName"),
                hw_model=node_data.get("hwModel"),
                role=node_data.get("role"),
                latitude=position.get("latitude") or position.get("lat"),
                longitude=position.get("longitude") or position.get("lon"),
                altitude=position.get("altitude") or position.get("alt"),
                position_precision_bits=position.get("precisionBits"),
                is_licensed=node_data.get("isLicensed", False),
            )
            if position.get("time"):
                node.position_time = datetime.fromtimestamp(
                    position["time"], tz=timezone.utc
                )
            if node_data.get("lastHeard"):
                node.last_heard = datetime.fromtimestamp(
                    node_data["lastHeard"], tz=timezone.utc
                )
            db.add(node)

    async def _collect_messages(self, client: httpx.AsyncClient, headers: dict) -> None:
        """Collect messages from the API."""
        try:
            response = await client.get(
                f"{self.source.url}/api/v1/messages",
                headers=headers,
                params={"limit": 100},
            )
            if response.status_code != 200:
                logger.warning(f"Failed to fetch messages: {response.status_code}")
                return

            data = response.json()
            messages_data = data if isinstance(data, list) else data.get("messages", [])

            async with async_session_maker() as db:
                for msg_data in messages_data:
                    await self._insert_message(db, msg_data)
                await db.commit()

            logger.debug(f"Collected {len(messages_data)} messages")
        except Exception as e:
            logger.error(f"Error collecting messages: {e}")

    async def _insert_message(self, db, msg_data: dict) -> None:
        """Insert a message if it doesn't exist."""
        packet_id = msg_data.get("packetId") or msg_data.get("id")
        if not packet_id:
            return

        # Check if message already exists
        result = await db.execute(
            select(Message).where(
                Message.source_id == self.source.id,
                Message.packet_id == packet_id,
            )
        )
        if result.scalar():
            return  # Already exists

        message = Message(
            source_id=self.source.id,
            packet_id=packet_id,
            from_node_num=msg_data.get("fromNodeNum") or msg_data.get("from"),
            to_node_num=msg_data.get("toNodeNum") or msg_data.get("to"),
            channel=msg_data.get("channel", 0),
            text=msg_data.get("text"),
            reply_id=msg_data.get("replyId"),
            emoji=msg_data.get("emoji"),
            hop_limit=msg_data.get("hopLimit"),
            hop_start=msg_data.get("hopStart"),
            rx_snr=msg_data.get("rxSnr"),
            rx_rssi=msg_data.get("rxRssi"),
        )
        if msg_data.get("rxTime"):
            message.rx_time = datetime.fromtimestamp(msg_data["rxTime"], tz=timezone.utc)
        db.add(message)

    async def _collect_telemetry(self, client: httpx.AsyncClient, headers: dict) -> None:
        """Collect telemetry from the API."""
        try:
            response = await client.get(
                f"{self.source.url}/api/v1/telemetry",
                headers=headers,
                params={"limit": 100},
            )
            if response.status_code != 200:
                logger.warning(f"Failed to fetch telemetry: {response.status_code}")
                return

            data = response.json()
            telemetry_data = data if isinstance(data, list) else data.get("telemetry", [])

            async with async_session_maker() as db:
                for telem in telemetry_data:
                    await self._insert_telemetry(db, telem)
                await db.commit()

            logger.debug(f"Collected {len(telemetry_data)} telemetry records")
        except Exception as e:
            logger.error(f"Error collecting telemetry: {e}")

    async def _insert_telemetry(self, db, telem_data: dict) -> None:
        """Insert telemetry data."""
        from app.models.telemetry import TelemetryType

        node_num = telem_data.get("nodeNum") or telem_data.get("from")
        if not node_num:
            return

        telem_type_str = telem_data.get("type", "device").lower()
        try:
            telem_type = TelemetryType(telem_type_str)
        except ValueError:
            telem_type = TelemetryType.DEVICE

        device_metrics = telem_data.get("deviceMetrics", {}) or {}
        env_metrics = telem_data.get("environmentMetrics", {}) or {}

        telemetry = Telemetry(
            source_id=self.source.id,
            node_num=node_num,
            telemetry_type=telem_type,
            battery_level=device_metrics.get("batteryLevel"),
            voltage=device_metrics.get("voltage"),
            channel_utilization=device_metrics.get("channelUtilization"),
            air_util_tx=device_metrics.get("airUtilTx"),
            uptime_seconds=device_metrics.get("uptimeSeconds"),
            temperature=env_metrics.get("temperature"),
            relative_humidity=env_metrics.get("relativeHumidity"),
            barometric_pressure=env_metrics.get("barometricPressure"),
        )
        db.add(telemetry)

    async def _collect_traceroutes(
        self, client: httpx.AsyncClient, headers: dict
    ) -> None:
        """Collect traceroutes from the API."""
        try:
            response = await client.get(
                f"{self.source.url}/api/v1/traceroutes/recent",
                headers=headers,
            )
            if response.status_code != 200:
                logger.warning(f"Failed to fetch traceroutes: {response.status_code}")
                return

            data = response.json()
            routes_data = data if isinstance(data, list) else data.get("traceroutes", [])

            async with async_session_maker() as db:
                for route in routes_data:
                    await self._insert_traceroute(db, route)
                await db.commit()

            logger.debug(f"Collected {len(routes_data)} traceroutes")
        except Exception as e:
            logger.error(f"Error collecting traceroutes: {e}")

    async def _insert_traceroute(self, db, route_data: dict) -> None:
        """Insert a traceroute."""
        traceroute = Traceroute(
            source_id=self.source.id,
            from_node_num=route_data.get("fromNodeNum") or route_data.get("from"),
            to_node_num=route_data.get("toNodeNum") or route_data.get("to"),
            route=route_data.get("route"),
            route_back=route_data.get("routeBack"),
            snr_towards=route_data.get("snrTowards"),
            snr_back=route_data.get("snrBack"),
        )
        db.add(traceroute)

    async def start(self) -> None:
        """Start periodic collection."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(f"Started MeshMonitor collector: {self.source.name}")

    async def _poll_loop(self) -> None:
        """Polling loop."""
        while self._running:
            try:
                await self.collect()
            except Exception as e:
                logger.error(f"Poll error: {e}")

            # Wait for next poll
            await asyncio.sleep(self.source.poll_interval_seconds)

    async def stop(self) -> None:
        """Stop periodic collection."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"Stopped MeshMonitor collector: {self.source.name}")
