# Running Pulsar Tests in Docker

This guide explains how to run your Pulsar integration tests inside a Docker container with Python 3.10 and the official `pulsar-client`.

---

## 1. Build the Dev Docker Image

From your `backend/` directory:

```sh
docker build -f app/core/pulsar/docker/Dockerfile.dev -t pulsar-python-dev .
```

---

## 2. Run the Container With Code Mounted

```sh
docker run -it --rm -v "C:/Users/tyriq/Documents/Github/lead_ignite_backend_3.0/backend:/app" pulsar-python-dev
```
Replace the path before `:/app` with your absolute project path if different.

---

## 3. Run Your Tests Inside the Container

```sh
poetry run pytest app/core/pulsar/_tests/test_client.py
```

---

## 4. Pulsar Service URL for Docker

Use this in your Python config to connect to your local Pulsar broker:

```python
PULSAR_SERVICE_URL = "pulsar://host.docker.internal:6650"
```

---

## 5. Troubleshooting

- Make sure your Pulsar Docker Compose cluster is running:
  ```sh
  docker-compose -f app/core/pulsar/docker/docker-compose.pulsar.yml up -d
  ```
- Check that your dependencies are installed in `pyproject.toml`.
- If you see import errors, verify your volume mount and Python path.

---

## 6. Example: One-Liner

```sh
docker run -it --rm -v "C:/Users/tyriq/Documents/Github/lead_ignite_backend_3.0/backend:/app" pulsar-python-dev poetry run pytest app/core/pulsar/_tests/test_client.py
```

---

For more details, see the Dockerfile and project README.
