FROM mcr.microsoft.com/playwright/python:v1.59.0-noble

# OCI standard annotations
LABEL org.opencontainers.image.title="autonomyx-playwright" \
      org.opencontainers.image.description="Playwright web scraper sidecar for Autonomyx Model Gateway" \
      org.opencontainers.image.source="https://github.com/openautonomyx/autonomyx-model-gateway" \
      org.opencontainers.image.vendor="OPENAUTONOMYX (OPC) PRIVATE LIMITED" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app

COPY scraper_server.py .

RUN pip install --no-cache-dir \
        fastapi==0.111.0 \
        uvicorn==0.30.0 \
        httpx==0.27.0 \
        pydantic==2.7.0 \
    && useradd -m scraper \
    && chown -R scraper /app

USER scraper

EXPOSE 8400
CMD ["python", "scraper_server.py"]
