"""Source management endpoints (admin only)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.middleware import require_admin
from app.database import get_db
from app.models import Source
from app.models.source import SourceType
from app.schemas.source import (
    MeshMonitorSourceCreate,
    MeshMonitorSourceUpdate,
    MqttSourceCreate,
    MqttSourceUpdate,
    SourceResponse,
    SourceTestResult,
)

router = APIRouter(prefix="/api/admin/sources", tags=["sources"])


@router.get("", response_model=list[SourceResponse])
async def list_sources(
    db: AsyncSession = Depends(get_db),
    _admin: None = Depends(require_admin),
) -> list[SourceResponse]:
    """List all configured sources."""
    result = await db.execute(select(Source).order_by(Source.name))
    sources = result.scalars().all()
    return [SourceResponse.model_validate(s) for s in sources]


@router.post("/meshmonitor", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_meshmonitor_source(
    source_data: MeshMonitorSourceCreate,
    db: AsyncSession = Depends(get_db),
    _admin: None = Depends(require_admin),
) -> SourceResponse:
    """Create a new MeshMonitor source."""
    source = Source(
        name=source_data.name,
        type=SourceType.MESHMONITOR,
        url=source_data.url,
        api_token=source_data.api_token,
        poll_interval_seconds=source_data.poll_interval_seconds,
        enabled=source_data.enabled,
    )
    db.add(source)
    await db.flush()
    await db.refresh(source)
    return SourceResponse.model_validate(source)


@router.post("/mqtt", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_mqtt_source(
    source_data: MqttSourceCreate,
    db: AsyncSession = Depends(get_db),
    _admin: None = Depends(require_admin),
) -> SourceResponse:
    """Create a new MQTT source."""
    source = Source(
        name=source_data.name,
        type=SourceType.MQTT,
        mqtt_host=source_data.mqtt_host,
        mqtt_port=source_data.mqtt_port,
        mqtt_username=source_data.mqtt_username,
        mqtt_password=source_data.mqtt_password,
        mqtt_topic_pattern=source_data.mqtt_topic_pattern,
        mqtt_use_tls=source_data.mqtt_use_tls,
        enabled=source_data.enabled,
    )
    db.add(source)
    await db.flush()
    await db.refresh(source)
    return SourceResponse.model_validate(source)


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: str,
    db: AsyncSession = Depends(get_db),
    _admin: None = Depends(require_admin),
) -> SourceResponse:
    """Get a specific source."""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return SourceResponse.model_validate(source)


@router.put("/meshmonitor/{source_id}", response_model=SourceResponse)
async def update_meshmonitor_source(
    source_id: str,
    source_data: MeshMonitorSourceUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: None = Depends(require_admin),
) -> SourceResponse:
    """Update a MeshMonitor source."""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if source.type != SourceType.MESHMONITOR:
        raise HTTPException(status_code=400, detail="Source is not a MeshMonitor source")

    update_data = source_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(source, field, value)

    await db.flush()
    await db.refresh(source)
    return SourceResponse.model_validate(source)


@router.put("/mqtt/{source_id}", response_model=SourceResponse)
async def update_mqtt_source(
    source_id: str,
    source_data: MqttSourceUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: None = Depends(require_admin),
) -> SourceResponse:
    """Update an MQTT source."""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if source.type != SourceType.MQTT:
        raise HTTPException(status_code=400, detail="Source is not an MQTT source")

    update_data = source_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(source, field, value)

    await db.flush()
    await db.refresh(source)
    return SourceResponse.model_validate(source)


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: str,
    db: AsyncSession = Depends(get_db),
    _admin: None = Depends(require_admin),
) -> None:
    """Delete a source and all its data."""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    await db.delete(source)


@router.post("/{source_id}/test", response_model=SourceTestResult)
async def test_source(
    source_id: str,
    db: AsyncSession = Depends(get_db),
    _admin: None = Depends(require_admin),
) -> SourceTestResult:
    """Test a source connection."""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    if source.type == SourceType.MESHMONITOR:
        from app.collectors.meshmonitor import MeshMonitorCollector

        collector = MeshMonitorCollector(source)
        return await collector.test_connection()
    else:
        from app.collectors.mqtt import MqttCollector

        collector = MqttCollector(source)
        return await collector.test_connection()
