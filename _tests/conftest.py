import os
# * Force Pulsar client to use localhost:6650 for tests (see config.py override)
# ! Windows Docker: Force IPv4 for Pulsar broker (localhost may resolve to ::1 and fail)
os.environ["PULSAR_TEST_LOCALHOST"] = "0"
os.environ["PULSAR_TEST_HOST"] = "127.0.0.1"
import subprocess  # ! Used for Docker commands
import time
from unittest.mock import patch

import pytest




@pytest.fixture(scope="session", autouse=True)
def ensure_pulsar_container() -> None:
    """
    * Ensure Pulsar Docker container is running before tests.
    * Starts the container if not running.
    """
    compose_file = os.path.join(os.path.dirname(__file__), "../docker/docker-compose.pulsar.yml")
    # * Use the correct Pulsar broker container name from docker-compose (was 'pulsar', should be 'broker')
    container_name = os.environ.get("PULSAR_BROKER_CONTAINER", "broker")  # Set env var to override if needed
    # If you change container_name in docker-compose, update here or set PULSAR_BROKER_CONTAINER
    import errno
    try:
        # ? Check if container is running
        result = subprocess.run([
            "docker", "ps", "--filter", f"name={container_name}", "--filter", "status=running", "--format", "{{.Names}}"
        ], capture_output=True, text=True, check=True)
        running = container_name in result.stdout
    except FileNotFoundError as e:
        raise RuntimeError("Docker CLI not found. Make sure Docker is installed and available in PATH inside the container.") from e
    except Exception as e:
        # Detect common Docker socket/daemon errors
        msg = str(e)
        if "permission denied" in msg.lower():
            raise RuntimeError("Permission denied when accessing Docker. Try running as root or mounting the Docker socket with correct permissions (-v /var/run/docker.sock:/var/run/docker.sock).") from e
        if "cannot connect to the docker daemon" in msg.lower() or "is the docker daemon running" in msg.lower():
            raise RuntimeError("Cannot connect to Docker daemon. Ensure Docker Desktop is running and the Docker socket is mounted into the container (-v /var/run/docker.sock:/var/run/docker.sock). On Windows, Docker Desktop must be started and the socket shared.") from e
        print(f"! Error checking Pulsar container: {e}")
        running = False
    if not running:
        print("* Pulsar container not running. Starting via docker-compose...")
        import shutil
        # Prefer 'docker-compose' if available, else fallback to 'docker compose'
        compose_cmd = None
        if shutil.which("docker-compose"):
            compose_cmd = ["docker-compose", "-f", compose_file, "up", "-d"]
        elif shutil.which("docker"):
            compose_cmd = ["docker", "compose", "-f", compose_file, "up", "-d"]
        else:
            raise RuntimeError("Neither 'docker-compose' nor 'docker compose' is available! Install Docker Compose v1 or v2.")
        try:
            result = subprocess.run(compose_cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"! Failed to start Pulsar container.\nCommand: {' '.join(compose_cmd)}\nExit code: {e.returncode}\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}")
            raise RuntimeError(f"Failed to start Pulsar container: {e}") from e
        # * Wait for container to be healthy
        for _ in range(30):
            result = subprocess.run([
                "docker", "inspect", "-f", "{{.State.Health.Status}}", container_name
            ], capture_output=True, text=True)
            if "healthy" in result.stdout:
                print("* Pulsar container is healthy.")
                break
            time.sleep(2)
        else:
            raise RuntimeError("! Pulsar container did not become healthy in time.")
    yield

@pytest.fixture(autouse=True)
def mock_pulsar_config():
    """Mock PulsarConfig for all tests"""
    with patch('app.core.pulsar.config.PulsarConfig') as mock_config:
        mock_config.SECURITY = {
            'service_role': 'test_role',
            'topic_roles': {
                'allowed_topic': ['test_role']
            }
        }
        mock_config.RETRY = {
            'max_retries': 3,
            'delay': 1.0
        }
        yield mock_config
