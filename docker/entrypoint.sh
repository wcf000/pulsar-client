#!/bin/bash
set -e

ROLE="${1:-broker}"

case "$ROLE" in
  zookeeper)
    echo "Starting Pulsar Zookeeper..."
    exec bash -c "bin/apply-config-from-env.py conf/zookeeper.conf && \
      bin/generate-zookeeper-config.sh conf/zookeeper.conf && \
      exec bin/pulsar zookeeper"
    ;;
  bookie)
    echo "Starting Pulsar Bookie..."
    exec bash -c "mkdir -p /pulsar/data/bookkeeper/ledgers/current && \
      bin/apply-config-from-env.py conf/bookkeeper.conf && \
      bin/pulsar bookie"
    ;;
  broker)
    echo "Starting Pulsar Broker..."
    exec bash -c "bin/apply-config-from-env.py conf/broker.conf && exec bin/pulsar broker"
    ;;
  pulsar-init)
    echo "Initializing Pulsar cluster metadata..."
    exec bin/pulsar initialize-cluster-metadata \
      --cluster ${CLUSTER_NAME:-cluster-a} \
      --zookeeper ${ZOOKEEPER_SERVERS:-zookeeper:2181} \
      --configuration-store ${CONFIGURATION_STORE:-zookeeper:2181} \
      --web-service-url ${WEB_SERVICE_URL:-http://broker:8081} \
      --broker-service-url ${BROKER_SERVICE_URL:-pulsar://broker:6650}"
    ;;
  *)
    echo "Unknown or unspecified role: $ROLE. Running as broker by default."
    exec bash -c "bin/apply-config-from-env.py conf/broker.conf && exec bin/pulsar broker"
    ;;
esac
