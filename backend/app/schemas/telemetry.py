"""Schemas for telemetry data."""

from datetime import datetime

from pydantic import BaseModel


class TelemetryResponse(BaseModel):
    """Response schema for telemetry data."""

    id: str
    source_id: str
    source_name: str | None = None
    node_num: int
    telemetry_type: str

    # Device metrics
    battery_level: int | None = None
    voltage: float | None = None
    channel_utilization: float | None = None
    air_util_tx: float | None = None
    uptime_seconds: int | None = None

    # Environment metrics
    temperature: float | None = None
    relative_humidity: float | None = None
    barometric_pressure: float | None = None

    # Power metrics
    current: float | None = None

    # Signal metrics
    snr_local: float | None = None
    snr_remote: float | None = None
    rssi: float | None = None

    # Timestamp
    received_at: datetime

    model_config = {"from_attributes": True}


class TelemetryHistoryPoint(BaseModel):
    """Single data point for telemetry graph."""

    timestamp: datetime
    source_id: str
    source_name: str | None = None
    value: float | None = None


class TelemetryHistory(BaseModel):
    """Historical telemetry data for a specific metric."""

    metric: str
    unit: str
    data: list[TelemetryHistoryPoint]
