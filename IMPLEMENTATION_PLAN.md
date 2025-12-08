# MeshManager Implementation Plan

## Overview

MeshManager is a management and oversight application that aggregates data from multiple MeshMonitor instances and Meshtastic MQTT servers. It provides a unified view of mesh network activity with Prometheus-compatible metrics for monitoring.

---

## Technology Decisions

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Backend | **FastAPI** (Python 3.11+) | Async support, OpenAPI docs, Pydantic validation |
| Frontend | **React 19 + Vite** | Consistency with MeshMonitor, shared component patterns |
| Database | **PostgreSQL 16** | Scalability, JSONB support, concurrent connections |
| MQTT Client | **aiomqtt** (async) | Native asyncio integration with FastAPI |
| Protobuf | **betterproto** or **protobuf** | Decode Meshtastic binary messages |
| ORM | **SQLAlchemy 2.0** (async) | Type-safe async database operations |
| Auth | **Authlib** | OIDC/OAuth2 client implementation |
| HTTP Client | **httpx** (async) | Poll MeshMonitor instances |
| Maps | **Leaflet + React-Leaflet** | Same as MeshMonitor |
| Styling | **Catppuccin** | Design requirement |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MeshManager                                  │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │   React     │  │   FastAPI   │  │  PostgreSQL │                  │
│  │  Frontend   │◄─┤   Backend   │◄─┤   Database  │                  │
│  │  (Vite)     │  │             │  │             │                  │
│  └─────────────┘  └──────┬──────┘  └─────────────┘                  │
│                          │                                           │
│         ┌────────────────┼────────────────┐                         │
│         ▼                ▼                ▼                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │ MeshMonitor │  │ MeshMonitor │  │    MQTT     │                  │
│  │  Collector  │  │  Collector  │  │  Collector  │                  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                  │
│         │                │                │                         │
└─────────┼────────────────┼────────────────┼─────────────────────────┘
          ▼                ▼                ▼
   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
   │ MeshMonitor │  │ MeshMonitor │  │ External    │
   │  Instance 1 │  │  Instance 2 │  │ MQTT Broker │
   └─────────────┘  └─────────────┘  └─────────────┘
```

---

## Project Structure

```
meshmanager/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application entry
│   │   ├── config.py               # Configuration (environment vars)
│   │   ├── database.py             # SQLAlchemy async engine
│   │   │
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── source.py           # MeshMonitor/MQTT source configs
│   │   │   ├── node.py             # Node records (per-source)
│   │   │   ├── message.py          # Text messages
│   │   │   ├── telemetry.py        # Telemetry data
│   │   │   ├── traceroute.py       # Traceroute records
│   │   │   ├── channel.py          # Channel configurations
│   │   │   ├── user.py             # User accounts (OIDC)
│   │   │   └── settings.py         # System settings
│   │   │
│   │   ├── schemas/                # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── source.py
│   │   │   ├── node.py
│   │   │   ├── metrics.py
│   │   │   └── auth.py
│   │   │
│   │   ├── routers/                # API routes
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # OIDC authentication
│   │   │   ├── sources.py          # Source management (admin)
│   │   │   ├── metrics.py          # Prometheus /metrics endpoint
│   │   │   ├── ui.py               # UI data endpoints (internal)
│   │   │   └── health.py           # Health check
│   │   │
│   │   ├── collectors/             # Data collection services
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # Abstract collector interface
│   │   │   ├── meshmonitor.py      # MeshMonitor API poller
│   │   │   └── mqtt.py             # MQTT subscriber
│   │   │
│   │   ├── services/               # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── collector_manager.py # Manages all collectors
│   │   │   ├── retention.py        # Data retention cleanup
│   │   │   └── protobuf.py         # Protobuf decoding
│   │   │
│   │   ├── auth/                   # Authentication
│   │   │   ├── __init__.py
│   │   │   ├── oidc.py             # OIDC client
│   │   │   └── middleware.py       # Auth middleware
│   │   │
│   │   └── utils/                  # Utilities
│   │       ├── __init__.py
│   │       └── meshtastic.py       # Meshtastic helpers
│   │
│   ├── migrations/                 # Alembic migrations
│   │   ├── env.py
│   │   └── versions/
│   │
│   ├── protobufs/                  # Meshtastic protobuf definitions (submodule)
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_collectors.py
│   │   ├── test_metrics.py
│   │   └── test_auth.py
│   │
│   ├── pyproject.toml              # Python dependencies (uv/pip)
│   ├── alembic.ini
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   │
│   │   ├── components/
│   │   │   ├── Layout/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── Layout.tsx
│   │   │   ├── Map/
│   │   │   │   ├── MapContainer.tsx
│   │   │   │   ├── NodeMarker.tsx
│   │   │   │   └── MapControls.tsx
│   │   │   ├── NodeList/
│   │   │   │   ├── NodeList.tsx
│   │   │   │   ├── NodeCard.tsx
│   │   │   │   └── NodeFilters.tsx
│   │   │   ├── Sources/
│   │   │   │   ├── SourceList.tsx
│   │   │   │   ├── AddMeshMonitorModal.tsx
│   │   │   │   └── AddMqttModal.tsx
│   │   │   ├── Settings/
│   │   │   │   ├── SettingsPanel.tsx
│   │   │   │   └── RetentionSettings.tsx
│   │   │   └── Auth/
│   │   │       ├── LoginButton.tsx
│   │   │       └── ProtectedRoute.tsx
│   │   │
│   │   ├── contexts/
│   │   │   ├── AuthContext.tsx
│   │   │   ├── DataContext.tsx
│   │   │   └── SettingsContext.tsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── useNodes.ts
│   │   │   ├── useSources.ts
│   │   │   ├── usePoll.ts
│   │   │   └── useAuth.ts
│   │   │
│   │   ├── services/
│   │   │   └── api.ts
│   │   │
│   │   ├── styles/
│   │   │   ├── catppuccin.css
│   │   │   └── global.css
│   │   │
│   │   └── types/
│   │       ├── node.ts
│   │       ├── source.ts
│   │       └── api.ts
│   │
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile
│
├── docker/
│   ├── nginx.conf                  # Reverse proxy config
│   └── init-db.sql                 # PostgreSQL initialization
│
├── docker-compose.yml              # Production
├── docker-compose.dev.yml          # Development
├── .env.example
├── PLAN.md
├── IMPLEMENTATION_PLAN.md
└── README.md
```

---

## Database Schema

### Sources Table
Stores configuration for MeshMonitor instances and MQTT connections.

```sql
CREATE TABLE sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('meshmonitor', 'mqtt')),

    -- MeshMonitor specific
    url VARCHAR(500),
    api_token VARCHAR(500),
    poll_interval_seconds INTEGER DEFAULT 300,

    -- MQTT specific
    mqtt_host VARCHAR(255),
    mqtt_port INTEGER DEFAULT 1883,
    mqtt_username VARCHAR(255),
    mqtt_password VARCHAR(500),
    mqtt_topic_pattern VARCHAR(500),  -- e.g., "msh/US/LongFast/#"
    mqtt_use_tls BOOLEAN DEFAULT FALSE,

    -- Common
    enabled BOOLEAN DEFAULT TRUE,
    last_poll_at TIMESTAMPTZ,
    last_error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Nodes Table
Stores node data, kept separate per source.

```sql
CREATE TABLE nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,

    node_num BIGINT NOT NULL,           -- Meshtastic node number
    node_id VARCHAR(20),                -- Hex ID (e.g., "!abcd1234")
    short_name VARCHAR(10),
    long_name VARCHAR(40),
    hw_model VARCHAR(50),
    role VARCHAR(30),

    -- Position
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    altitude INTEGER,
    position_time TIMESTAMPTZ,
    position_precision_bits INTEGER,

    -- Status
    last_heard TIMESTAMPTZ,
    is_licensed BOOLEAN DEFAULT FALSE,

    -- Timestamps
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(source_id, node_num)
);

CREATE INDEX idx_nodes_source ON nodes(source_id);
CREATE INDEX idx_nodes_last_heard ON nodes(last_heard);
CREATE INDEX idx_nodes_position ON nodes(latitude, longitude) WHERE latitude IS NOT NULL;
```

### Messages Table

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,

    packet_id BIGINT,
    from_node_num BIGINT NOT NULL,
    to_node_num BIGINT,
    channel INTEGER DEFAULT 0,
    text TEXT,

    -- Reply/reaction
    reply_id BIGINT,
    emoji VARCHAR(10),

    -- Metadata
    hop_limit INTEGER,
    hop_start INTEGER,
    rx_time TIMESTAMPTZ,
    rx_snr REAL,
    rx_rssi INTEGER,

    received_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(source_id, packet_id)
);

CREATE INDEX idx_messages_source ON messages(source_id);
CREATE INDEX idx_messages_time ON messages(received_at);
CREATE INDEX idx_messages_from ON messages(from_node_num);
```

### Telemetry Table

```sql
CREATE TABLE telemetry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    node_num BIGINT NOT NULL,

    telemetry_type VARCHAR(30) NOT NULL,  -- 'device', 'environment', 'power', 'air_quality'

    -- Device metrics
    battery_level INTEGER,
    voltage REAL,
    channel_utilization REAL,
    air_util_tx REAL,
    uptime_seconds BIGINT,

    -- Environment metrics
    temperature REAL,
    relative_humidity REAL,
    barometric_pressure REAL,

    -- Power metrics
    current REAL,

    received_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_telemetry_source ON telemetry(source_id);
CREATE INDEX idx_telemetry_node ON telemetry(node_num);
CREATE INDEX idx_telemetry_time ON telemetry(received_at);
CREATE INDEX idx_telemetry_type ON telemetry(telemetry_type);
```

### Traceroutes Table

```sql
CREATE TABLE traceroutes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,

    from_node_num BIGINT NOT NULL,
    to_node_num BIGINT NOT NULL,

    route BIGINT[],           -- Array of node numbers in path
    route_back BIGINT[],      -- Return path
    snr_towards REAL[],       -- SNR at each hop towards
    snr_back REAL[],          -- SNR at each hop back

    received_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_traceroutes_source ON traceroutes(source_id);
CREATE INDEX idx_traceroutes_from ON traceroutes(from_node_num);
CREATE INDEX idx_traceroutes_to ON traceroutes(to_node_num);
CREATE INDEX idx_traceroutes_time ON traceroutes(received_at);
```

### Channels Table

```sql
CREATE TABLE channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,

    channel_index INTEGER NOT NULL,
    name VARCHAR(12),
    role VARCHAR(20),  -- 'primary', 'secondary', 'disabled'

    uplink_enabled BOOLEAN DEFAULT FALSE,
    downlink_enabled BOOLEAN DEFAULT FALSE,
    position_precision INTEGER,

    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(source_id, channel_index)
);
```

### Users Table (OIDC)

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    oidc_subject VARCHAR(255) UNIQUE NOT NULL,
    oidc_issuer VARCHAR(500) NOT NULL,

    email VARCHAR(255),
    display_name VARCHAR(255),

    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);
```

### Settings Table

```sql
CREATE TABLE settings (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Example settings:
-- retention.messages_days: 30
-- retention.telemetry_days: 7
-- retention.traceroutes_days: 30
-- ui.default_map_center: {"lat": 39.8283, "lng": -98.5795}
-- ui.default_zoom: 4
```

---

## Prometheus Metrics

Endpoint: `GET /metrics`

### Node Metrics
```
# Node battery level (0-100)
meshmanager_node_battery_level{source="source_name", node_id="!abcd1234", short_name="NODE1"} 85

# Node voltage
meshmanager_node_voltage{source="source_name", node_id="!abcd1234"} 4.12

# Node last heard timestamp (Unix seconds)
meshmanager_node_last_heard_timestamp{source="source_name", node_id="!abcd1234"} 1702000000

# Node uptime in seconds
meshmanager_node_uptime_seconds{source="source_name", node_id="!abcd1234"} 86400

# Node channel utilization (0-100)
meshmanager_node_channel_utilization{source="source_name", node_id="!abcd1234"} 12.5

# Node air utilization TX (0-100)
meshmanager_node_air_util_tx{source="source_name", node_id="!abcd1234"} 5.2

# GPS accuracy (position precision bits)
meshmanager_node_position_precision_bits{source="source_name", node_id="!abcd1234"} 32
```

### Network Metrics
```
# Total active nodes per source (heard in last hour)
meshmanager_active_nodes_total{source="source_name"} 42

# Total nodes ever seen per source
meshmanager_nodes_total{source="source_name"} 156

# Messages received (counter)
meshmanager_messages_received_total{source="source_name", channel="0"} 1234

# Messages received in last hour
meshmanager_messages_last_hour{source="source_name"} 45

# Traceroutes received (counter)
meshmanager_traceroutes_received_total{source="source_name"} 89

# Average route hops
meshmanager_route_avg_hops{source="source_name"} 2.3

# Route success rate (nodes reachable)
meshmanager_route_success_rate{source="source_name"} 0.85
```

### System/Source Metrics
```
# Source collection status (1=healthy, 0=error)
meshmanager_source_healthy{source="source_name", type="meshmonitor"} 1

# Last successful collection timestamp
meshmanager_source_last_collection_timestamp{source="source_name"} 1702000000

# Collection errors (counter)
meshmanager_source_errors_total{source="source_name"} 2

# Database row counts
meshmanager_db_rows_total{table="nodes"} 500
meshmanager_db_rows_total{table="messages"} 10000
meshmanager_db_rows_total{table="telemetry"} 50000
```

---

## API Endpoints

### Public (No Auth Required)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/metrics` | Prometheus metrics |
| GET | `/health` | Health check |
| GET | `/api/nodes` | List all nodes (UI polling) |
| GET | `/api/sources` | List sources (names only) |

### Admin (OIDC Auth Required)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/admin/sources` | List sources with full config |
| POST | `/api/admin/sources` | Create source |
| PUT | `/api/admin/sources/{id}` | Update source |
| DELETE | `/api/admin/sources/{id}` | Delete source |
| POST | `/api/admin/sources/{id}/test` | Test source connection |
| GET | `/api/admin/settings` | Get all settings |
| PUT | `/api/admin/settings/{key}` | Update setting |
| POST | `/api/admin/retention/run` | Trigger retention cleanup |

### Authentication
| Method | Path | Description |
|--------|------|-------------|
| GET | `/auth/login` | Initiate OIDC login |
| GET | `/auth/callback` | OIDC callback |
| POST | `/auth/logout` | Logout |
| GET | `/auth/status` | Current user info |

---

## Data Collection

### MeshMonitor Collector
- Polls each configured MeshMonitor instance every 5 minutes (configurable)
- Uses MeshMonitor's `/api/v1/` endpoints:
  - `/api/v1/network/nodes` - All nodes
  - `/api/v1/messages` - Recent messages
  - `/api/v1/telemetry` - Telemetry data
  - `/api/v1/traceroutes/recent` - Recent traceroutes
- Handles pagination for large datasets
- Stores with source_id reference
- Tracks last poll time and errors

### MQTT Collector
- Connects to external MQTT broker
- Subscribes to user-configured topic patterns
- Decodes both protobuf and JSON formats:
  - Protobuf: Standard Meshtastic binary encoding
  - JSON: When device has JSON MQTT mode enabled
- Processes packet types:
  - `TEXT_MESSAGE_APP` - Text messages
  - `POSITION_APP` - Position updates
  - `TELEMETRY_APP` - Telemetry data
  - `TRACEROUTE_APP` - Traceroute responses
  - `NODEINFO_APP` - Node information
- Handles reconnection with exponential backoff

---

## Authentication Flow

1. User clicks "Login" button
2. Frontend redirects to `/auth/login`
3. Backend initiates OIDC authorization request
4. User authenticates with OIDC provider
5. Provider redirects to `/auth/callback`
6. Backend validates tokens, creates/updates user
7. Session cookie set, redirect to frontend
8. Frontend polls `/auth/status` to get user info

### First Admin Setup
- First OIDC user to log in becomes admin
- Admins can grant admin rights to other users
- Non-admins can view read-only UI

---

## Frontend Features

### Main Layout
- **Header**: App name, source status indicators, login button
- **Left Sidebar**: Collapsible node list with filtering
- **Main Area**: Leaflet map with node markers
- **Right Panel (optional)**: Node details when selected

### Node List
- Grouped by source
- Sortable by: name, last heard, battery, distance
- Filterable by: source, role, online status
- Click to center map on node

### Map
- Leaflet with Catppuccin-styled tiles (or neutral tiles)
- Node markers with status colors (online/offline/unknown)
- Popups with node details
- Optional: Route lines between connected nodes

### Admin Panel (authenticated)
- Add/edit/remove MeshMonitor sources
- Add/edit/remove MQTT sources
- Test source connections
- Configure retention periods
- View collection logs/errors

---

## Docker Compose

### Production (`docker-compose.yml`)
```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: meshmanager
      POSTGRES_USER: meshmanager
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U meshmanager"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
    environment:
      DATABASE_URL: postgresql+asyncpg://meshmanager:${POSTGRES_PASSWORD}@postgres/meshmanager
      OIDC_ISSUER: ${OIDC_ISSUER}
      OIDC_CLIENT_ID: ${OIDC_CLIENT_ID}
      OIDC_CLIENT_SECRET: ${OIDC_CLIENT_SECRET}
      SESSION_SECRET: ${SESSION_SECRET}
    depends_on:
      postgres:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./docker/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - frontend
      - backend

volumes:
  postgres_data:
```

### Development (`docker-compose.dev.yml`)
```yaml
services:
  postgres:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: meshmanager
      POSTGRES_USER: meshmanager
      POSTGRES_PASSWORD: devpassword
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data

  backend:
    build:
      context: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://meshmanager:devpassword@postgres/meshmanager
      DEBUG: "true"
    volumes:
      - ./backend:/app
    depends_on:
      - postgres

  frontend:
    build:
      context: ./frontend
      target: development
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      VITE_API_URL: http://localhost:8000

volumes:
  postgres_dev_data:
```

---

## Implementation Phases

### Phase 1: Foundation
- Project scaffolding (backend + frontend)
- PostgreSQL schema with Alembic migrations
- Basic FastAPI app with health endpoint
- React app with Vite, routing, Catppuccin theme

### Phase 2: Data Collection
- MeshMonitor collector (API polling)
- MQTT collector (protobuf + JSON decoding)
- Background task scheduler (asyncio)
- Source management API

### Phase 3: Prometheus Metrics
- Metrics endpoint implementation
- Node metrics (battery, voltage, GPS, uptime)
- Network metrics (counts, activity)
- Source health metrics

### Phase 4: Frontend UI
- Node list component with filtering
- Leaflet map integration
- Source status display
- Polling for updates

### Phase 5: Authentication
- OIDC integration
- Session management
- Admin panel for source configuration
- Protected routes

### Phase 6: Polish
- Retention cleanup job
- Error handling and logging
- Docker production build
- Documentation

---

## Configuration Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host/db

# OIDC Authentication
OIDC_ISSUER=https://your-idp.com
OIDC_CLIENT_ID=meshmanager
OIDC_CLIENT_SECRET=secret
OIDC_REDIRECT_URI=http://localhost:8080/auth/callback

# Session
SESSION_SECRET=your-secret-key

# Application
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173

# Defaults
DEFAULT_POLL_INTERVAL=300
DEFAULT_RETENTION_DAYS=30
```

---

## Dependencies

### Backend (Python)
```toml
[project]
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.30",
    "alembic>=1.14",
    "pydantic>=2.10",
    "pydantic-settings>=2.6",
    "httpx>=0.28",
    "aiomqtt>=2.3",
    "betterproto>=2.0.0b7",
    "authlib>=1.3",
    "itsdangerous>=2.2",
    "python-multipart>=0.0.17",
    "prometheus-client>=0.21",
]
```

### Frontend (Node.js)
```json
{
  "dependencies": {
    "react": "^19.0",
    "react-dom": "^19.0",
    "react-router-dom": "^7.0",
    "@tanstack/react-query": "^5.60",
    "leaflet": "^1.9",
    "react-leaflet": "^5.0",
    "axios": "^1.7"
  },
  "devDependencies": {
    "vite": "^6.0",
    "typescript": "^5.7",
    "@types/react": "^19.0",
    "@types/leaflet": "^1.9",
    "@catppuccin/palette": "^1.0"
  }
}
```
