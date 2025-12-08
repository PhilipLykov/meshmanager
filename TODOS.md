# MeshManager TODOs

## Completed

### Planning
- [x] Review MeshMonitor codebase architecture
- [x] Create comprehensive implementation plan (IMPLEMENTATION_PLAN.md)

### Phase 1: Foundation
- [x] Create backend project scaffolding (FastAPI + SQLAlchemy)
- [x] Create frontend project scaffolding (React + Vite)
- [x] Set up PostgreSQL schema with Alembic migrations
- [x] Implement Catppuccin theme

### Phase 2: Data Collection
- [x] Implement MeshMonitor collector (API polling)
- [x] Implement MQTT collector (protobuf + JSON)
- [x] Create source management API
- [x] Background task scheduler (collector_manager.py)

### Phase 3: Prometheus Metrics
- [x] Implement /metrics endpoint
- [x] Node metrics (battery, voltage, GPS, uptime)
- [x] Network metrics (counts, activity)
- [x] Source health metrics

### Phase 4: Frontend UI
- [x] Node list component with filtering
- [x] Leaflet map integration
- [x] Source status display
- [x] Polling updates

### Phase 5: Authentication
- [x] OIDC integration
- [x] Session management
- [x] Admin panel (basic)
- [x] Protected routes

### Phase 6: Polish
- [x] Data retention cleanup job
- [x] Docker production build
- [x] Docker development build
- [x] Documentation (README.md)

## Future Enhancements
- [ ] Admin UI for managing sources (currently placeholder)
- [ ] Settings page for retention configuration
- [ ] Node detail panel
- [ ] Message history view
- [ ] Traceroute visualization
- [ ] Unit and integration tests
