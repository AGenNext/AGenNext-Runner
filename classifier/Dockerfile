FROM python:3.12-slim

LABEL org.opencontainers.image.title="autonomyx-classifier" \
      org.opencontainers.image.description="Task classifier sidecar for Autonomyx Model Gateway — routes prompts to optimal models" \
      org.opencontainers.image.source="https://github.com/openautonomyx/autonomyx-model-gateway" \
      org.opencontainers.image.vendor="OPENAUTONOMYX (OPC) PRIVATE LIMITED" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app

COPY classifier_server.py training_data.json ./

RUN pip install --no-cache-dir \
        sentence-transformers==3.0.1 \
        scikit-learn==1.5.0 \
        fastapi==0.111.0 \
        uvicorn==0.30.0 \
        numpy==1.26.4 \
        joblib==1.4.2 \
    && useradd -m classifier \
    && chown -R classifier /app

USER classifier

EXPOSE 8100
CMD ["uvicorn", "classifier_server:app", "--host", "0.0.0.0", "--port", "8100"]
