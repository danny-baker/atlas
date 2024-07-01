###########
# BUILDER #
###########

# pull base docker image (lightweight ubuntu)
FROM python:3.8.1-slim-buster as builder

# set work directory
WORKDIR /usr/src/app

# set environment variables (for robustness)
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc

# update pip
RUN pip install --upgrade pip

# install python dependencies
COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /usr/src/app/wheels -r requirements.txt

# this should have build a temporary base image with all the dependencies, now we build the final

#########
# FINAL #
#########

# pull official base image
FROM python:3.8.1-slim-buster

# create directory for the app user
RUN mkdir -p /home/app

# create the app user (non root)
#RUN addgroup -S app && adduser -S app -G app
RUN addgroup --system app && adduser --system --group app

# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
WORKDIR $APP_HOME

# install dependencies
RUN apt-get update
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache /wheels/*

# delete all compiled wheels
RUN rm -f -r /wheels

# copy project to container
COPY . $APP_HOME

# chown all the files to the app user and switch to the app user
RUN chown -R app:app $APP_HOME
USER app

#Expose port 8050 in the container (can be mapped to another port on host)
EXPOSE 8050

# start gunicorn and specify workers and threads
ENTRYPOINT gunicorn --bind 0.0.0.0:8050 wsgi:app --timeout=0 --workers GUNICORN_WORKERS --worker-class gthread --threads GUNICORN_THREADS
