# Builds the Python web app linux container.

FROM python:3.8.1-slim-buster

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

#Expose port 8050 in the container (can be mapped to another port on host)
EXPOSE 8050

# start gunicorn and specify workers and threads
ENTRYPOINT gunicorn --bind 0.0.0.0:8050 wsgi:app --timeout=0 --workers GUNICORN_WORKERS --worker-class gthread --threads GUNICORN_THREADS


