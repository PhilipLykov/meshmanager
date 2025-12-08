"""UI data endpoints (internal use for frontend)."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Node, Source
from app.schemas.node import NodeResponse, NodeSummary

router = APIRouter(prefix="/api", tags=["ui"])


class SourceSummary:
    """Simple source summary for public display."""

    def __init__(self, id: str, name: str, type: str, enabled: bool, last_poll_at: datetime | None):
        self.id = id
        self.name = name
        self.type = type
        self.enabled = enabled
        self.last_poll_at = last_poll_at


@router.get("/sources")
async def list_sources_public(
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List sources (public, names only)."""
    result = await db.execute(select(Source).order_by(Source.name))
    sources = result.scalars().all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "type": s.type.value,
            "enabled": s.enabled,
            "healthy": s.enabled and s.last_error is None,
        }
        for s in sources
    ]


@router.get("/nodes", response_model=list[NodeSummary])
async def list_nodes(
    db: AsyncSession = Depends(get_db),
    source_id: str | None = Query(default=None, description="Filter by source ID"),
    active_only: bool = Query(default=False, description="Only show nodes heard in last hour"),
) -> list[NodeSummary]:
    """List all nodes across all sources."""
    query = select(Node, Source.name.label("source_name")).join(Source)

    if source_id:
        query = query.where(Node.source_id == source_id)

    if active_only:
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        query = query.where(Node.last_heard >= one_hour_ago)

    query = query.order_by(Node.last_heard.desc().nullslast())

    result = await db.execute(query)
    rows = result.all()

    return [
        NodeSummary(
            id=node.id,
            source_id=node.source_id,
            source_name=source_name,
            node_num=node.node_num,
            node_id=node.node_id,
            short_name=node.short_name,
            long_name=node.long_name,
            latitude=node.latitude,
            longitude=node.longitude,
            last_heard=node.last_heard,
        )
        for node, source_name in rows
    ]


@router.get("/nodes/{node_id}", response_model=NodeResponse)
async def get_node(
    node_id: str,
    db: AsyncSession = Depends(get_db),
) -> NodeResponse:
    """Get a specific node by ID."""
    result = await db.execute(
        select(Node, Source.name.label("source_name"))
        .join(Source)
        .where(Node.id == node_id)
    )
    row = result.first()
    if not row:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Node not found")

    node, source_name = row
    response = NodeResponse.model_validate(node)
    response.source_name = source_name
    return response
