# Use official Playwright image — has Chromium + all deps pre-installed
# Much more reliable than installing manually
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi==0.111.0 \
    uvicorn==0.30.0 \
    httpx==0.27.0 \
    pydantic==2.7.0

COPY scraper_server.py .

# Non-root user
RUN useradd -m scraper && chown -R scraper /app
USER scraper

EXPOSE 8400
CMD ["python", "scraper_server.py"]
