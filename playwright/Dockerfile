# ── Stage 1: Dependencies (cached layer) ─────────────────────────────────
FROM python:3.12-slim AS deps

WORKDIR /app

# System deps for Chromium only (not Firefox/WebKit)
# Keeps image at ~650MB vs 2.1GB for all browsers
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 \
    libgbm1 libasound2 libpango-1.0-0 libcairo2 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Chromium only — playwright install chromium is ~350MB
# vs all browsers at ~1.2GB
RUN playwright install chromium --with-deps

# ── Stage 2: App ──────────────────────────────────────────────────────────
FROM deps AS app

WORKDIR /app
COPY scraper_server.py .

# Non-root user — prevents container escape attacks
RUN useradd -m scraper
USER scraper

EXPOSE 8400

CMD ["python", "scraper_server.py"]
