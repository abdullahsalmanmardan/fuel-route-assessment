FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app/backend

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY documents /app/documents
COPY backend .

RUN python manage.py migrate --noinput \
    && python manage.py import_stations \
    && useradd --system --create-home app \
    && chown -R app /app

USER app
EXPOSE 8000

# One worker: the response cache is in-process.
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "8", "--access-logfile", "-"]
