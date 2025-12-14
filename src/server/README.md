# Term Tac Toe Server

Self-hosting guide for the Term Tac Toe WebSocket game server.

## Prerequisites

- Docker & Docker Compose
- (Optional) Python 3.11+ for local development

## Quick Start with Docker

### 1. Navigate to Server Directory

```bash
cd server
```

### 2. Start the Server

```bash
docker compose up
```

The server will be available at `http://localhost:8000`

## Configuration

### Environment Variables

Set in `.env`:

```
MYSQL_USERNAME="root"
MYSQL_PASSWORD="oursql1234"
MYSQL_HOST="localhost"
MYSQL_PORT=3306
DB_NAME="tictactoe"
DB_POOL_SIZE=5
DB_POOL_RECYCLE=1800
```

### Port Binding

Edit `compose.yml` to change the exposed port:

```yaml
services:
  server:
    ports:
      - "8000:8000" # Change first number to desired port
```

## Architecture

- **Framework**: FastAPI + Starlette WebSockets
- **Database**: PostgreSQL
- **Web Server**: Uvicorn
- **Reverse Proxy**: Caddy (optional, configured in Caddyfile)

## Development

### Local Setup

```bash
cd server
uv sync
```

### Run Locally

```bash
uv run uvicorn app:app --reload
```

Server runs on `http://localhost:8000`

## Deployment

### Docker Hub

```bash
docker build -t your-registry/term-tac-toe:latest .
docker push your-registry/term-tac-toe:latest
```

### Production Considerations

- Use environment variables for sensitive data
- Enable HTTPS with a reverse proxy (Caddy configured)
- Set up database backups
- Monitor WebSocket connections
- Consider horizontal scaling with a load balancer

## Troubleshooting

**Database connection failed?** Check `.env` and ensure MySQL is running.

**Port already in use?** Modify the port mapping in `compose.yml`.

**WebSocket connection timeout?** Verify firewall rules and server logs with:

```bash
docker compose logs server
```
