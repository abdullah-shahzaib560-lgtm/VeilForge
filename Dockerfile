FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml requirements.txt ./
COPY src/ ./src/
COPY README.md LICENSE ./

RUN pip install --no-cache-dir -e .

ENTRYPOINT ["veilforge"]
CMD ["--help"]
