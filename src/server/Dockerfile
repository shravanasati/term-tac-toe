# Build stage
FROM python:3.11-slim as builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock .
COPY src/server/pyproject.toml ./src/server/pyproject.toml
COPY src/common ./src/common

# Create virtual environment and install dependencies
RUN uv sync --frozen --no-cache

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port (adjust if your FastAPI app uses a different port)
EXPOSE 8000

# Run the FastAPI application with uvicorn
CMD ["/app/.venv/bin/fastapi", "run", "./src/server/app.py", "--host", "0.0.0.0", "--port", "8000"]
