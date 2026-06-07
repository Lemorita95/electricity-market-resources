#!/bin/sh
set -e

echo "Running database bootstrap..."
python -m app.bootstrap.init_db

echo "Starting application..."
exec python src/app/main.py