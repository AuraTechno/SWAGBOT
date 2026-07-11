#!/bin/bash
set -e

echo "=== SWAG VPN Bot Update ==="

cd "$(dirname "$0")"

echo "[1/4] Pulling latest code from GitHub..."
git pull origin main

echo "[2/4] Rebuilding Docker image..."
docker compose build --no-cache

echo "[3/4] Stopping old container..."
docker compose down

echo "[4/4] Starting new container..."
docker compose up -d

echo ""
echo "=== Update complete! ==="
docker compose logs --tail=20
