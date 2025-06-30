#!/bin/bash
# Script to completely reset Pulsar Docker environment

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Stop all Pulsar containers
echo "Stopping all Pulsar containers..."
docker-compose -f docker-compose.pulsar.yml down

# Remove all Pulsar volumes
echo "Removing all Pulsar volumes..."
docker volume rm docker_bookie-data docker_pulsar-zookeeper-data 2>/dev/null || true

# Make sure we don't have cached data from previous runs
echo "Pruning Docker system..."
docker system prune -f --volumes --filter "label=service=pulsar" 2>/dev/null || true

# Start fresh
echo "Starting fresh Pulsar environment..."
docker-compose -f docker-compose.pulsar.yml up -d

# Wait for services to initialize
echo "Waiting for services to initialize..."
sleep 15

# Show container status
echo "Checking container status:"
docker ps -f "name=bookie" --format "{{.Names}} - {{.Status}}"
docker ps -f "name=broker" --format "{{.Names}} - {{.Status}}"
docker ps -f "name=zookeeper" --format "{{.Names}} - {{.Status}}"

echo "Pulsar environment has been completely reset."
echo "Run 'docker logs bookie' to check for any remaining errors."
