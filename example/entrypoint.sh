#!/usr/bin/env bash

set -e

gunicorn -w 4 -k uvicorn.workers.UvicornWorker proxyx.app:app --bind 0.0.0.0
