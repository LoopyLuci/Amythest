FROM python:3.11-slim AS final
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .
COPY . .
EXPOSE 8125
CMD ["uvicorn", "amythest.backend.server:app", "--host", "0.0.0.0", "--port", "8125"]
