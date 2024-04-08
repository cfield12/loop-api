FROM python:3.8
LABEL maintainer="charlie.field@gmail.com"
ENV PYTHONUNBUFFERED 1

# Main installs.
RUN apt-get update
RUN apt-get install -y apt-utils

RUN apt-get install -y git openssh-server
RUN apt-get install -y libjpeg-dev libfreetype6-dev libpng-dev
RUN apt-get install -y gcc zlib1g-dev libssl-dev musl-dev libffi-dev

RUN python -m pip install --upgrade pip
RUN python -m pip install importlib-resources setuptools wheel pyOpenSSL==23.2.0

COPY ./docker/data_pipeline/requirements.txt requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt
