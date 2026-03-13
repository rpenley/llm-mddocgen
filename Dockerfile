FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY pyproject.toml README.md /app/
COPY llm_mddocgen /app/llm_mddocgen

RUN pip install --no-cache-dir .

ENTRYPOINT ["python", "-m", "llm_mddocgen"]
CMD ["--help"]
