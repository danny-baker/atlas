# Builds the Python web app linux container.

FROM python:3.8.1-slim-buster

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8050

# start gunicorn and specify workers and threads (these are injected at build via github actions from repository variables)
ENTRYPOINT gunicorn --bind 0.0.0.0:8050 wsgi:app --timeout=0 --workers GUNICORN_WORKERS --worker-class gthread --threads GUNICORN_THREADS


