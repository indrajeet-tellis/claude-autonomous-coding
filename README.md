# Agent Dashboard with VNC

A full-stack autonomous coding agent platform with a Next.js dashboard, VNC desktop access, and PostgreSQL persistence.

## Quick Start

### 1. Set up environment

```bash
cd /Volumes/Storage/Documents/claude-quickstarts/docker-autonomous-agent

# Copy and edit environment file
cp .env.example .env
# Edit .env and add your MiniMax API key
```

### 2. Build and run

```bash
# Build all containers
docker compose build

# Start the stack
docker compose up -d

# View logs
docker compose logs -f
```

### 3. Access the dashboard

| Service | URL |
|---------|-----|
| **Dashboard** | http://localhost:3001 |
| **VNC Desktop** | http://localhost:6080/vnc.html |
| **API** | http://localhost:8000 |

**Default credentials:**
- Dashboard: `admin` / `admin123`
- VNC Password: `agentpass`

## Features

### Dashboard (Next.js)
- **Tasks Tab**: Create, edit, and monitor tasks
- **Logs Tab**: Real-time log viewer with WebSocket
- **Screenshots Tab**: Gallery of browser screenshots
- **VNC Tab**: Embedded desktop view
- **Settings Tab**: Toggle headless/GUI mode

### VNC Desktop
- Ubuntu 22.04 with XFCE
- Pre-installed: Chrome, VS Code, Node.js, Python
- 1920x1080 resolution
- Accessible via browser (noVNC)

### Agent
- Fully autonomous (no permission prompts)
- Hybrid Chrome mode (GUI/headless toggle)
- Progress tracking via dashboard
- Real-time logging

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         docker-compose                           │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  PostgreSQL  │  │   FastAPI    │  │   Next.js    │           │
│  │  (Port 5432) │◄─│  (Port 8000) │◄─│  (Port 3001) │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│         │                 │                                      │
│         │                 ▼                                      │
│         │         ┌──────────────┐                              │
│         │         │   Desktop    │                              │
│         │         │  VNC + Agent │                              │
│         │         │  (Port 6080) │                              │
│         │         └──────────────┘                              │
│         │                                                        │
│  📁 postgres_data  📁 workspace  📁 screenshots                  │
└─────────────────────────────────────────────────────────────────┘
```

## Commands

```bash
# Build containers
docker compose build

# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down

# Reset database
docker compose down -v
docker compose up -d
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_BASE_URL` | API endpoint | `https://api.minimax.io/anthropic` |
| `ANTHROPIC_API_KEY` | Your API key | (required) |
| `ANTHROPIC_MODEL` | Model name | `MiniMax-M2` |
| `ADMIN_USERNAME` | Dashboard username | `admin` |
| `ADMIN_PASSWORD` | Dashboard password | `admin123` |
| `VNC_PASSWORD` | VNC password | `agentpass` |
| `VNC_RESOLUTION` | Desktop resolution | `1920x1080` |
| `AGENT_HEADLESS` | Start in headless mode | `false` |

## Tech Stack

- **Frontend**: Next.js 14, shadcn/ui, Zustand, TanStack Query, Zod
- **Backend**: FastAPI, Prisma, PostgreSQL
- **Desktop**: Ubuntu 22.04, XFCE, TigerVNC, noVNC
- **Agent**: Python, Anthropic SDK, Puppeteer

## License

MIT
