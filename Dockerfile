# Builds the Python web app linux container.
# https://hub.docker.com/_/python and basically just choose the image that has the python version you want preinstalled

FROM python:3.12.7-slim

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --upgrade pip setuptools wheel

RUN pip install --upgrade pip 

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8050

# start gunicorn and specify workers and threads (Defaults are "workers 1" and "threads 1".)
# These are overwritten at build via github actions from repository variables). 
# Changing them here will be a breaking change for the build (as it uses pattern matching)

ENTRYPOINT gunicorn --bind 0.0.0.0:8050 wsgi:app --timeout=0 --workers 1 --worker-class gthread --threads 1


