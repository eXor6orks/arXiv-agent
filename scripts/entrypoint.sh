#!/bin/sh
set -e

python scripts/bootstrap.py

exec uvicorn api.main:app --host 0.0.0.0 --port 8000
