FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY src /app/src

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uvicorn", "hue_async.web.app:app", "--host", "0.0.0.0", "--port", "8000"]