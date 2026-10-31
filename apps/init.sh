#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
docker compose -f "$SCRIPT_DIR/docker-compose.yml" up --build -d --wait --wait-timeout 180
echo "Monolith: http://localhost:8080/api/v1/sensors"
echo "Temperature simulator: http://localhost:8081/docs"
echo "Devices service: http://localhost:8082/docs"
echo "Telemetry service: http://localhost:8083/docs"
