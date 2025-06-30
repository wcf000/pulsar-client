@echo off
REM Script to completely reset Pulsar Docker environment

REM Stop all Pulsar containers
echo Stopping all Pulsar containers...
docker-compose -f docker-compose.pulsar.yml down

REM Remove all Pulsar volumes
echo Removing all Pulsar volumes...
docker volume rm docker_bookie-data docker_pulsar-zookeeper-data 2>nul || echo Volumes not found or already removed.

REM Start fresh
echo Starting fresh Pulsar environment...
docker-compose -f docker-compose.pulsar.yml up -d

echo Pulsar environment has been completely reset.
