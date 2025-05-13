# Pulsar Integration Troubleshooting Log

## Overview
This document tracks the troubleshooting steps, what worked, and recommendations for future Pulsar integration debugging. It is intended as a living reference for both CI and local development.

---

## Context
- **Goal:** Run integration tests against a real Pulsar broker (not mocks) from both Windows and WSL2, ensuring the Python Pulsar client can reliably connect to the broker at `localhost:6650`.
- **Stack:** Docker Compose (broker, bookie, zookeeper), Pulsar Python client, pytest.

---

## Troubleshooting Steps & Observations

### 1. Docker Compose Network and Port Mapping
- Confirmed broker service exposes `6650:6650` and `8081:8080`.
- Verified with `docker compose ps` that broker is mapped to `0.0.0.0:6650->6650/tcp`.
- Confirmed with `python -c "import socket; ..."` that `localhost:6650` is reachable from host.

### 2. Broker Environment Variables
- Set `advertisedListeners` to:
  ```
  - advertisedListeners=external:pulsar://localhost:6650,internal:pulsar://broker:6650
  ```
- **Removed** `advertisedAddress=broker` (to allow Pulsar to auto-advertise correct address).
- Restarted broker after each config change.

### 3. Broker Health
- Broker container always reported as healthy in Docker Compose.
- `docker compose logs --tail 100 broker` shows normal health checks and no fatal errors.

### 4. Connectivity Tests
- Host-to-broker port test (`python ...`) returns `OK`.
- Broker-to-broker port test (`python ...` inside container) returns `OK`.

### 5. Integration Test Failures
- Python Pulsar client fails with `RuntimeError: Could not connect to Pulsar on localhost or 127.0.0.1`.
- Confirmed client is using `pulsar://localhost:6650`.
- No TLS or auth enabled.

---

## What Worked
- Port mapping and network config are correct (TCP connections succeed).
- Removing `advertisedAddress=broker` avoids common Docker hostname confusion.

## What Did Not Work
- Changing only `advertisedListeners` without removing `advertisedAddress`.
- Restarting broker without config changes.
- Relying on default Pulsar Docker Compose settings for host access.

---

## Next Steps & Recommendations

1. **Check Broker Logs for Advertised Listeners**
   - Look for `advertisedListeners` and `Listening on` lines.
   - Ensure broker advertises `pulsar://localhost:6650` for external clients.

2. **Test with Pulsar CLI**
   - From host: `docker run --rm --network=host apachepulsar/pulsar:3.1.0 bin/pulsar-client produce -m "test" -n 1 pulsar://localhost:6650/my-topic`
   - If this fails, it's a broker config issue, not Python.

3. **Check for Firewalls/Antivirus**
   - On Windows, ensure nothing is blocking non-HTTP traffic to 6650.

4. **Try Tests from WSL2**
   - If running from Windows fails, try from WSL2 shell.

5. **Update Docs**
   - Keep this file updated with new troubleshooting steps and solutions.

---

## Summary
- **Network and port mapping are correct.**
- **Broker config (`advertisedListeners`) is critical.**
- **If TCP works but Pulsar client fails, check protocol-level logs and advertised addresses.**

---

*Last updated: 2025-05-13*
