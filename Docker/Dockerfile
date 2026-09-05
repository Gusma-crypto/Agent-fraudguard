FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN addgroup --system fraudguard \
    && adduser --system --ingroup fraudguard --home /nonexistent --no-create-home fraudguard

COPY pyproject.toml ./
COPY src/fraudguard_agent ./src/fraudguard_agent
RUN pip install --no-cache-dir .

USER fraudguard
EXPOSE 3000
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "from urllib.request import urlopen; urlopen('http://127.0.0.1:3000/health', timeout=2).read()"]
CMD ["uvicorn", "fraudguard_agent.main:app", "--host", "0.0.0.0", "--port", "3000"]

FROM runtime AS test
USER root
COPY tests ./tests
COPY scripts ./scripts
COPY skills ./skills
COPY openclaw-workspace ./openclaw-workspace
RUN pip install --no-cache-dir '.[dev]'
CMD ["pytest", "-q"]
