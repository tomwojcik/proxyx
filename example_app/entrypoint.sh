#!/usr/bin/env bash

set -e

uvicorn proxyx.app:app --host 0.0.0.0 --port 8000 --reload
