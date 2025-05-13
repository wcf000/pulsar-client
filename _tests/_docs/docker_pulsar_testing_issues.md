# Pulsar Docker Integration Testing Issues (Windows/WSL2)

## Overview
This document summarizes the issues, root causes, and attempted solutions encountered when running Pulsar integration tests using Docker on Windows, with a focus on host/container networking and Python test execution.

---

## Issues Faced

### 1. **Pulsar Client Connection Timeouts**
- **Symptom:** Python Pulsar client (`pulsar-client`) fails to connect to the broker (`localhost:6650` or `127.0.0.1:6650`) with repeated connection timeouts and retry loops.
- **Root Cause:**
  - Pulsar broker inside Docker advertises itself as an internal Docker hostname (e.g., `broker`), but host-based clients resolve `localhost` to IPv6 (`::1`) or the wrong interface.
  - Docker for Windows/WSL2 has complex port forwarding and networking quirks.
  - Pulsar's C++/Python client is sensitive to mismatches between advertised address, listener, and client connection target.

### 2. **Dockerfile COPY Context Errors**
- **Symptom:** Docker build fails with `CreateFile .../app: The system cannot find the file specified.`
- **Root Cause:**
  - Confusion between Docker build context (set in Compose) and Dockerfile location.
  - COPY paths must always be relative to the build context, not the Dockerfile.
  - Windows pathing and case-sensitivity can cause additional confusion.

### 3. **Cannot Shell Into Broker Container for Testing**
- **Symptom:** `docker-compose exec broker /bin/bash` or `/bin/sh` fails with `stat C:/Program Files/Git/usr/bin/bash: no such file or directory`.
- **Root Cause:**
  - Running Docker Compose from Git Bash/MinGW on Windows causes Docker to map `/bin/bash` to the host's Git Bash, not the container shell.
  - Only works from native Command Prompt or PowerShell.

### 4. **Broker Container Lacks Python Test Environment**
- **Symptom:** Even when shelling into the broker, there is no `app/` code, `poetry`, or Python dependencies to run tests.
- **Root Cause:**
  - The broker image is a Pulsar runtime, not a Python app runtime.
  - Python tests and dependencies are not present unless a dedicated app/test container is built.

---

## Documentation and References

- [Pulsar Docker Compose Example](https://pulsar.apache.org/docs/standalone-docker/)
- [Docker Compose Build Context Docs](https://docs.docker.com/compose/compose-file/compose-file-v3/#build)
- [GitHub Issue: Pulsar Client Docker Networking](https://github.com/apache/pulsar/issues/13080)
- [Docker for Windows Networking](https://docs.docker.com/desktop/windows/networking/)
- [Stack Overflow: Docker Compose COPY Context Confusion](https://stackoverflow.com/questions/49158445/)
- [Git Bash and Docker Compose Shell Issues](https://github.com/docker/for-win/issues/1829)

---

## Lessons Learned / Best Practices

- Always run `docker-compose exec ... /bin/bash` from Command Prompt or PowerShell on Windows.
- Use a dedicated app/test container for Python integration tests, not the Pulsar broker image.
- Set Docker build context to the project root and COPY paths relative to that context.
- Prefer `pulsar://broker:6650` for in-Docker networking, not `localhost`.
- Document and automate these patterns for future contributors.

---

## todo
- [ ] Scaffold a dedicated Python test-runner container for integration testing.
- [ ] Add CI/CD documentation for cross-platform Pulsar testing.
- [ ] Provide troubleshooting steps for common Windows Docker issues.
