# FastAPI Pulsar Messaging Suite

**Production-ready Python/FastAPI Messaging, Streaming, and Event Processing Stack**

This module provides robust, scalable, and observable messaging for Python microservices using:

- **Apache Pulsar** (streaming, messaging, event-driven architecture)
- **Async Python Client** (non-blocking, scalable consumers/producers)
- **Docker Compose** (orchestration, multi-node)
- **Pytest & Pydantic** (testing, type safety)

---

## 📁 Folder Structure & Conventions

```
pulsar/
├── _docs/           # Markdown docs, best practices, diagrams, usage
├── _tests/          # Unit/integration tests for all core logic
├── config.py        # Singleton config (class-based, imports from global settings)
├── docker/          # Dockerfile, docker-compose, Pulsar configs, .env.example
├── models/          # Pydantic models or message schemas
├── exceptions/      # Custom exceptions for messaging
├── data/            # Example data, schemas, or test fixtures
├── <core>.py        # Main implementation (client.py, decorators.py, health_check.py, etc.)
├── README.md        # Main readme (this file)
```

- **_docs/**: All documentation, diagrams, and best practices for this module.
- **_tests/**: All tests for this module, including integration, failover, and performance tests.
- **config.py**: Singleton config pattern, imports from global settings, exposes all constants for this module.
- **docker/**: Containerization assets (Dockerfile, docker-compose, Pulsar configs, .env.example, etc).
- **models/**: Pydantic models or message schemas for typed payloads and validation.
- **exceptions/**: Custom exception classes for robust error handling.
- **data/**: Example/test data, schemas, or fixtures for integration and load tests.
- **<core>.py**: Main implementation modules (e.g., client.py, decorators.py, health_check.py, etc).

---

## 🏗️ Singleton & Config Pattern
- Use a single class (e.g., `PulsarConfig`) in `config.py` to centralize all env, broker, and integration settings.
- Import from global settings to avoid duplication and ensure DRY config.
- Document all config keys in `_docs/usage.md` and in this README.

---

## 📄 Documentation & Testing
- Place all best practices, diagrams, and usage guides in `_docs/`.
- All tests (unit, integration, smoke, failover, performance) go in `_tests/` with clear naming.
- Use `_tests/_docs/` for test-specific docs if needed.

---

## 🐳 Docker & Pulsar Configs
- Place Dockerfile(s), docker-compose, and Pulsar configs in `docker/`.
- Provide `.env.example` for local/dev/prod setups.
- Document multi-node and local development setups in `_docs/` and this README.

---

## 🔐 Required Environment Variables

See `.env.example` for all required environment variables for Pulsar, authentication, and integration.

---

## 📦 Usage

1. **Clone this repo or add as a submodule.**
2. **Configure environment variables as per `.env.example`.**
3. **Build and start services:**
   ```bash
   docker-compose -f docker/docker-compose.pulsar.yml up --build
   ```
4. **Access Pulsar admin at:** http://localhost:8080 (default)
5. **Run integration and failover tests as needed.**

---

## 🏷️ Tags

`python, fastapi, pulsar, messaging, streaming, event-driven, docker, pytest, pydantic`
