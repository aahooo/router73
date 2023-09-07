FROM ubuntu:20.04

RUN apt-get -yqq update \
 && apt-get install -y --no-install-recommends openssl curl gunicorn python3-pip \
 && python3 -m pip install arrow flask flask_simplelogin requests

COPY admin-ui/ /opt/admin-ui

WORKDIR /opt/admin-ui
