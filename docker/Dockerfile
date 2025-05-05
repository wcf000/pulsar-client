# Use official Apache Pulsar image as base
FROM apachepulsar/pulsar:latest

# Set working directory
WORKDIR /pulsar

# Copy entrypoint script to allow multi-role (pulsar, zookeeper, broker, bookie, init)
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Optional: Copy pulsar-ssl.conf for SSL/TLS support (if present)
# COPY docker/pulsar-ssl.conf /pulsar/conf/pulsar-ssl.conf

# Data volume for persistent storage
VOLUME ["/pulsar/data"]

# Expose common Pulsar ports (can be overridden in compose)
EXPOSE 6650 8080 8081 2181
EXPOSE 6651 8443 8444 2182  

# Default entrypoint delegates to script (role determined by CMD or env)
ENTRYPOINT ["/entrypoint.sh"]

# Default command (can be overridden in docker-compose)
CMD ["broker"]

# ---
# Example usage in docker-compose:
#  - To run as zookeeper:
#      command: zookeeper
#  - To run as bookie:
#      command: bookie
#  - To run as broker:
#      command: broker
#  - To run as pulsar-init:
#      command: pulsar-init
#
# All configuration is expected via environment variables or docker-compose.
# Healthchecks for each role should be set in compose, not here.
#
# To enable SSL/TLS, mount your certs to /pulsar/certs and use the provided pulsar-ssl.conf.
# Uncomment the COPY line and add relevant config to broker.conf, bookkeeper.conf, etc.
# See https://pulsar.apache.org/docs/next/security-tls-transport/ for advanced SSL usage and tuning.