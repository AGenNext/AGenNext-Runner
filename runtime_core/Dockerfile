# AGenNext Runtime Core
# Production Dockerfile with security hardening

# ── Build Stage ─────────────────────────────────────────────────────────────
FROM python:3.13-slim-bookworm AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install runtime dependencies
COPY runtime_core/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip wheel && \
    pip install --no-cache-dir -r requirements.txt


# ── Production Stage ───────────────────────────────────────────────────────
FROM python:3.13-slim-bookworm AS production

# ── Security: Non-root user ────────────────────────────────────────────────
RUN groupadd --gid 1000 runtime && \
    useradd --uid 1000 --gid runtime --shell /bin/false --create-home runtime

# ── Security: Read-only filesystem preparation ─────────────────────────
RUN mkdir -p /home/runtime/app /home/runtime/tmp /home/runtime/logs && \
    chown -R runtime:runtime /home/runtime

WORKDIR /home/runtime/app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application
COPY --chown=runtime:runtime runtime_core/ ./runtime_core/

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    RUNTIME_MAX_PAYLOAD_KEYS=256 \
    IDEMPOTENCY_TTL_SECONDS=3600 \
    SESSION_TTL_SECONDS=3600 \
    ENABLE_METRICS=true

# ── Security: Drop capabilities ─────────────────────────────────────────────
USER runtime

# ── Health Check ───────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8081/health')" || exit 1

# Expose port
EXPOSE 8081

# Run application
CMD ["uvicorn", "runtime_core.main:app", "--host", "0.0.0.0", "--port", "8081"]