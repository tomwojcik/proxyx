FROM python:3.9-slim

WORKDIR /opt/

COPY proxyx.yaml .
COPY .env .

ENV PROXYX_ROUTING_CONFIG_PATH=/opt/proxyx.yaml
ENV PROXYX_APP_CONFIG_PATH=/opt/.env

RUN python -m pip install --no-cache-dir -U proxyx

COPY entrypoint.sh .

ENTRYPOINT /opt/entrypoint.sh
