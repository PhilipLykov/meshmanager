"""MQTT collector for Meshtastic data."""

import asyncio
import json
import logging
from datetime import UTC, datetime

import aiomqtt

from app.collectors.base import BaseCollector
from app.database import async_session_maker
from app.models import Channel, Message, Node, Source, Telemetry
from app.schemas.source import SourceTestResult
from app.services.protobuf import decode_meshtastic_packet

logger = logging.getLogger(__name__)


class MqttCollector(BaseCollector):
    """Collector for MQTT sources."""

    def __init__(self, source: Source):
        super().__init__(source)
        self._running = False
        self._task: asyncio.Task | None = None
        self._client: aiomqtt.Client | None = None

    async def test_connection(self) -> SourceTestResult:
        """Test connection to the MQTT broker."""
        if not self.source.mqtt_host:
            return SourceTestResult(success=False, message="No MQTT host configured")

        try:
            async with aiomqtt.Client(
                hostname=self.source.mqtt_host,
                port=self.source.mqtt_port or 1883,
                username=self.source.mqtt_username,
                password=self.source.mqtt_password,
                tls_context=None,  # TODO: Add TLS support
            ) as client:
                # Subscribe briefly to test
                if self.source.mqtt_topic_pattern:
                    await client.subscribe(self.source.mqtt_topic_pattern)

                return SourceTestResult(
                    success=True,
                    message="Connection successful",
                )
        except aiomqtt.MqttError as e:
            return SourceTestResult(success=False, message=f"MQTT error: {e}")
        except Exception as e:
            return SourceTestResult(success=False, message=f"Connection error: {e}")

    async def collect(self) -> None:
        """MQTT uses continuous streaming, not polling."""
        pass

    async def start(self) -> None:
        """Start MQTT subscription."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._subscribe_loop())
        logger.info(f"Started MQTT collector: {self.source.name}")

    async def _subscribe_loop(self) -> None:
        """Main MQTT subscription loop with reconnection."""
        while self._running:
            try:
                async with aiomqtt.Client(
                    hostname=self.source.mqtt_host or "localhost",
                    port=self.source.mqtt_port or 1883,
                    username=self.source.mqtt_username,
                    password=self.source.mqtt_password,
                ) as client:
                    self._client = client

                    # Subscribe to configured topic
                    if self.source.mqtt_topic_pattern:
                        await client.subscribe(self.source.mqtt_topic_pattern)
                        logger.info(
                            f"Subscribed to {self.source.mqtt_topic_pattern} "
                            f"on {self.source.mqtt_host}"
                        )

                    # Update source status
                    await self._update_source_status(None)

                    # Process messages
                    async for message in client.messages:
                        if not self._running:
                            break
                        await self._process_message(message)

            except aiomqtt.MqttError as e:
                logger.error(f"MQTT error for {self.source.name}: {e}")
                await self._update_source_status(str(e))
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Unexpected error in MQTT loop: {e}")
                await self._update_source_status(str(e))

            if self._running:
                # Reconnect after delay
                logger.info(f"Reconnecting to {self.source.name} in 10 seconds...")
                await asyncio.sleep(10)

    async def _update_source_status(self, error: str | None) -> None:
        """Update source status in database."""
        try:
            async with async_session_maker() as db:
                from sqlalchemy import select

                result = await db.execute(
                    select(Source).where(Source.id == self.source.id)
                )
                source = result.scalar()
                if source:
                    source.last_poll_at = datetime.now(UTC)
                    source.last_error = error
                    await db.commit()
        except Exception as e:
            logger.error(f"Failed to update source status: {e}")

    async def _process_message(self, message: aiomqtt.Message) -> None:
        """Process an incoming MQTT message."""
        try:
            topic = str(message.topic)
            payload = message.payload
            logger.debug(f"Received MQTT message: topic={topic}, payload_len={len(payload) if isinstance(payload, bytes) else 'N/A'}")

            # Try to decode as JSON first
            try:
                if isinstance(payload, bytes):
                    data = json.loads(payload.decode("utf-8"))
                else:
                    data = json.loads(payload)
                logger.debug(f"Decoded JSON message: type={data.get('type')}, from={data.get('from') or data.get('fromId')}")
                await self._process_json_message(topic, data)
                return
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.debug(f"Failed to decode as JSON: {e}")
                pass

            # Try to decode as protobuf
            if isinstance(payload, bytes):
                logger.debug("Attempting protobuf decode")
                await self._process_protobuf_message(topic, payload)

        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}", exc_info=True)

    async def _process_json_message(self, topic: str, data: dict) -> None:
        """Process a JSON-encoded Meshtastic message."""
        msg_type = data.get("type", "").lower()
        logger.debug(f"Processing JSON message: type={msg_type}, topic={topic}, keys={list(data.keys())}")

        async with async_session_maker() as db:
            await self._ensure_channel(db, data)
            if msg_type == "text" or "text" in data:
                logger.debug("Handling as text message")
                await self._handle_text_message(db, data)
            elif msg_type == "position" or "position" in data:
                logger.debug("Handling as position message")
                await self._handle_position(db, data)
            elif msg_type == "telemetry" or "telemetry" in data:
                logger.debug("Handling as telemetry message")
                await self._handle_telemetry(db, data)
            elif msg_type == "nodeinfo" or "nodeinfo" in data:
                logger.debug("Handling as nodeinfo message")
                await self._handle_nodeinfo(db, data)
            else:
                logger.debug(f"Message type '{msg_type}' not handled, skipping")

            await db.commit()

    async def _ensure_channel(self, db, data: dict) -> None:
        """Ensure a channel record exists for MQTT messages."""
        channel_index = data.get("channel")
        if channel_index is None:
            return
        try:
            channel_index = int(channel_index)
        except (TypeError, ValueError):
            return

        from sqlalchemy import select

        result = await db.execute(
            select(Channel).where(
                Channel.source_id == self.source.id,
                Channel.channel_index == channel_index,
            )
        )
        channel = result.scalar()
        if channel:
            return

        channel = Channel(
            source_id=self.source.id,
            channel_index=channel_index,
            name=data.get("channel_name") or data.get("channelName"),
        )
        db.add(channel)

    async def _process_protobuf_message(self, topic: str, payload: bytes) -> None:
        """Process a protobuf-encoded Meshtastic message."""
        try:
            decoded = decode_meshtastic_packet(payload)
            if decoded:
                async with async_session_maker() as db:
                    await self._handle_decoded_packet(db, decoded)
                    await db.commit()
        except Exception as e:
            logger.debug(f"Failed to decode protobuf: {e}")

    async def _handle_text_message(self, db, data: dict) -> None:
        """Handle a text message."""
        from_node = data.get("from") or data.get("fromId")
        if not from_node:
            return

        # Convert hex ID to number if needed
        if isinstance(from_node, str) and from_node.startswith("!"):
            from_node = int(from_node[1:], 16)

        to_node = data.get("to") or data.get("toId")
        if isinstance(to_node, str) and to_node.startswith("!"):
            to_node = int(to_node[1:], 16)

        rx_time = self._parse_rx_time(data.get("rxTime"))

        message = Message(
            source_id=self.source.id,
            packet_id=data.get("id"),
            from_node_num=from_node,
            to_node_num=to_node,
            channel=data.get("channel", 0),
            text=data.get("text") or data.get("payload"),
            hop_limit=data.get("hopLimit"),
            hop_start=data.get("hopStart"),
            rx_time=rx_time,
            rx_snr=data.get("rxSnr"),
            rx_rssi=data.get("rxRssi"),
        )
        db.add(message)
        logger.debug(f"Received text message from {from_node}")

    @staticmethod
    def _parse_rx_time(value) -> datetime | None:
        if value is None:
            return None
        try:
            if isinstance(value, (int, float)):
                ts = float(value)
                if ts > 2_000_000_000_000:
                    ts = ts / 1000.0
                return datetime.fromtimestamp(ts, UTC)
            if isinstance(value, str):
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (TypeError, ValueError, OSError):
            return None
        return None

    async def _handle_position(self, db, data: dict) -> None:
        """Handle a position update."""
        from app.models.telemetry import TelemetryType

        from_node = data.get("from") or data.get("fromId")
        if not from_node:
            return

        if isinstance(from_node, str) and from_node.startswith("!"):
            from_node = int(from_node[1:], 16)

        position = data.get("position", data)
        lat = position.get("latitude") or position.get("lat")
        lon = position.get("longitude") or position.get("lon")
        alt = position.get("altitude") or position.get("alt")

        # Parse rx_time for telemetry records
        rx_time = self._parse_rx_time(data.get("rxTime")) or datetime.now(UTC)

        # Update or create node
        from sqlalchemy import select

        result = await db.execute(
            select(Node).where(
                Node.source_id == self.source.id,
                Node.node_num == from_node,
            )
        )
        node = result.scalar()

        if node:
            node.latitude = lat
            node.longitude = lon
            node.altitude = alt
            node.position_time = datetime.now(UTC)
            node.last_heard = datetime.now(UTC)
        else:
            node = Node(
                source_id=self.source.id,
                node_num=from_node,
                latitude=lat,
                longitude=lon,
                altitude=alt,
                position_time=datetime.now(UTC),
                last_heard=datetime.now(UTC),
            )
            db.add(node)

        # Create Telemetry records for Coverage Map (requires latitude/longitude in Telemetry table)
        # Check for existing records to avoid unique constraint violations
        if lat is not None:
            # Check if record already exists
            existing_lat = await db.execute(
                select(Telemetry).where(
                    Telemetry.source_id == self.source.id,
                    Telemetry.node_num == from_node,
                    Telemetry.metric_name == "latitude",
                    Telemetry.received_at == rx_time,
                )
            )
            if not existing_lat.scalar_one_or_none():
                lat_telemetry = Telemetry(
                    source_id=self.source.id,
                    node_num=from_node,
                    metric_name="latitude",
                    telemetry_type=TelemetryType.POSITION,
                    latitude=lat,
                    received_at=rx_time,
                )
                db.add(lat_telemetry)

        if lon is not None:
            # Check if record already exists
            existing_lon = await db.execute(
                select(Telemetry).where(
                    Telemetry.source_id == self.source.id,
                    Telemetry.node_num == from_node,
                    Telemetry.metric_name == "longitude",
                    Telemetry.received_at == rx_time,
                )
            )
            if not existing_lon.scalar_one_or_none():
                lon_telemetry = Telemetry(
                    source_id=self.source.id,
                    node_num=from_node,
                    metric_name="longitude",
                    telemetry_type=TelemetryType.POSITION,
                    longitude=lon,
                    received_at=rx_time,
                )
                db.add(lon_telemetry)

        logger.debug(f"Received position from {from_node}")

    async def _handle_telemetry(self, db, data: dict) -> None:
        """Handle telemetry data."""
        from app.models.telemetry import TelemetryType
        from sqlalchemy import select

        from_node = data.get("from") or data.get("fromId")
        if not from_node:
            return

        if isinstance(from_node, str) and from_node.startswith("!"):
            from_node = int(from_node[1:], 16)

        telem = data.get("telemetry", data)
        device_metrics = telem.get("deviceMetrics", {})
        env_metrics = telem.get("environmentMetrics", {})

        # Parse rx_time for telemetry records
        rx_time = self._parse_rx_time(data.get("rxTime")) or datetime.now(UTC)

        # Create separate Telemetry records for each metric (required for Utilization overlay and proper querying)
        # Device metrics
        if device_metrics:
            metrics_to_create = [
                ("batteryLevel", "battery_level", device_metrics.get("batteryLevel"), int),
                ("voltage", "voltage", device_metrics.get("voltage"), float),
                ("channelUtilization", "channel_utilization", device_metrics.get("channelUtilization"), float),
                ("airUtilTx", "air_util_tx", device_metrics.get("airUtilTx"), float),
                ("uptimeSeconds", "uptime_seconds", device_metrics.get("uptimeSeconds"), int),
            ]

            for metric_name, field_name, value, value_type in metrics_to_create:
                if value is not None:
                    # Check if record already exists
                    existing = await db.execute(
                        select(Telemetry).where(
                            Telemetry.source_id == self.source.id,
                            Telemetry.node_num == from_node,
                            Telemetry.metric_name == metric_name,
                            Telemetry.received_at == rx_time,
                        )
                    )
                    if not existing.scalar_one_or_none():
                        # Build kwargs for the specific metric field
                        kwargs = {
                            "source_id": self.source.id,
                            "node_num": from_node,
                            "metric_name": metric_name,
                            "telemetry_type": TelemetryType.DEVICE,
                            "received_at": rx_time,
                            field_name: value_type(value),
                        }
                        telemetry = Telemetry(**kwargs)
                        db.add(telemetry)

        # Environment metrics
        if env_metrics:
            metrics_to_create = [
                ("temperature", "temperature", env_metrics.get("temperature"), float),
                ("relativeHumidity", "relative_humidity", env_metrics.get("relativeHumidity"), float),
                ("barometricPressure", "barometric_pressure", env_metrics.get("barometricPressure"), float),
            ]

            for metric_name, field_name, value, value_type in metrics_to_create:
                if value is not None:
                    # Check if record already exists
                    existing = await db.execute(
                        select(Telemetry).where(
                            Telemetry.source_id == self.source.id,
                            Telemetry.node_num == from_node,
                            Telemetry.metric_name == metric_name,
                            Telemetry.received_at == rx_time,
                        )
                    )
                    if not existing.scalar_one_or_none():
                        # Build kwargs for the specific metric field
                        kwargs = {
                            "source_id": self.source.id,
                            "node_num": from_node,
                            "metric_name": metric_name,
                            "telemetry_type": TelemetryType.ENVIRONMENT,
                            "received_at": rx_time,
                            field_name: value_type(value),
                        }
                        telemetry = Telemetry(**kwargs)
                        db.add(telemetry)

        logger.debug(f"Received telemetry from {from_node}")

    async def _handle_nodeinfo(self, db, data: dict) -> None:
        """Handle node info update."""
        from_node = data.get("from") or data.get("fromId")
        if not from_node:
            return

        if isinstance(from_node, str) and from_node.startswith("!"):
            from_node = int(from_node[1:], 16)

        nodeinfo = data.get("nodeinfo", data)
        user = nodeinfo.get("user", {})

        from sqlalchemy import select

        result = await db.execute(
            select(Node).where(
                Node.source_id == self.source.id,
                Node.node_num == from_node,
            )
        )
        node = result.scalar()

        if node:
            node.node_id = user.get("id")
            node.short_name = user.get("shortName")
            node.long_name = user.get("longName")
            node.hw_model = user.get("hwModel")
            node.role = user.get("role")
            node.is_licensed = user.get("isLicensed", False)
            node.last_heard = datetime.now(UTC)
        else:
            node = Node(
                source_id=self.source.id,
                node_num=from_node,
                node_id=user.get("id"),
                short_name=user.get("shortName"),
                long_name=user.get("longName"),
                hw_model=user.get("hwModel"),
                role=user.get("role"),
                is_licensed=user.get("isLicensed", False),
                last_heard=datetime.now(UTC),
            )
            db.add(node)

        logger.debug(f"Received nodeinfo from {from_node}")

    async def _handle_decoded_packet(self, db, decoded: dict) -> None:
        """Handle a decoded protobuf packet."""
        portnum = decoded.get("portnum", "")

        if portnum == "TEXT_MESSAGE_APP":
            await self._handle_text_message(db, decoded)
        elif portnum == "POSITION_APP":
            await self._handle_position(db, decoded)
        elif portnum == "TELEMETRY_APP":
            await self._handle_telemetry(db, decoded)
        elif portnum == "NODEINFO_APP":
            await self._handle_nodeinfo(db, decoded)

    async def stop(self) -> None:
        """Stop MQTT subscription."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"Stopped MQTT collector: {self.source.name}")
