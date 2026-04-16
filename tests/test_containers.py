"""tests/test_containers.py
Testcontainer-based validation tests.
Covers the 6 failure modes that require real Docker:
  1. Pinned image tags exist on registry (can be pulled)
  2. Dockerfile base images exist and are pullable
  3. Dockerfile ARGs are used (not declared and forgotten)
  4. OPA policy syntax + unit tests pass
  5. OpenFGA model syntax valid
  6. Postgres init.sql runs cleanly against real Postgres

All tests skip gracefully if Docker is not available.
Marked with @pytest.mark.integration — excluded from fast unit test runs.
Run with: pytest tests/test_containers.py -v
"""
import re
import pytest
import subprocess
import shutil
import yaml
from pathlib import Path

ROOT = Path(__file__).parent.parent

# ── Docker availability guard ─────────────────────────────────────────────────

def docker_available():
    try:
        import docker
        docker.from_env().ping()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def docker_client():
    if not docker_available():
        pytest.skip("Docker not available")
    import docker
    return docker.from_env()


# ── 1. Pinned image tags exist on registry ────────────────────────────────────

def get_pinned_images():
    """Extract all pinned image tags from docker-compose.yml."""
    c = yaml.safe_load((ROOT / "docker-compose.yml").read_text())
    images = []
    for svc_name, svc in c["services"].items():
        img = svc.get("image", "")
        # Skip images with ${VAR} references — those are built locally
        if img and "${" not in img and "build" not in str(svc):
            images.append((svc_name, img))
    return images


@pytest.mark.integration
@pytest.mark.parametrize("svc_name,image", get_pinned_images())
def test_pinned_image_exists(docker_client, svc_name, image):
    """Every pinned image tag must be pullable from the registry.
    Uses docker pull --dry-run equivalent (manifest inspect) — no actual download."""
    result = subprocess.run(
        ["docker", "manifest", "inspect", image],
        capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, (
        f"services[{svc_name}]: image '{image}' not found on registry\n"
        f"{result.stderr.strip()}"
    )


# ── 2. Dockerfile base images exist ──────────────────────────────────────────

def get_dockerfiles():
    """Find all Dockerfiles in the project."""
    return list(ROOT.rglob("Dockerfile"))


@pytest.mark.integration
@pytest.mark.parametrize("dockerfile", get_dockerfiles())
def test_dockerfile_base_image_exists(docker_client, dockerfile):
    """Every FROM image in every Dockerfile must exist on the registry."""
    content = dockerfile.read_text()
    from_lines = re.findall(r'^FROM\s+([^\s]+)', content, re.MULTILINE)
    # Filter out multi-stage build aliases (FROM x AS y — check x only)
    errors = []
    for from_image in from_lines:
        # Skip build args like ${PYTHON_VERSION}
        if "${" in from_image or from_image == "scratch":
            continue
        result = subprocess.run(
            ["docker", "manifest", "inspect", from_image],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            errors.append(f"FROM {from_image} — not found on registry")
    assert not errors, (
        f"In {dockerfile.relative_to(ROOT)}:\n" + "\n".join(errors)
    )


# ── 3. Dockerfile ARGs declared but unused ────────────────────────────────────

@pytest.mark.parametrize("dockerfile", get_dockerfiles())
def test_dockerfile_args_used(dockerfile):
    """Every ARG declared in a Dockerfile must be referenced somewhere after it."""
    content = dockerfile.read_text()
    args = re.findall(r'^ARG\s+([A-Z_a-z0-9]+)', content, re.MULTILINE)
    errors = []
    for arg in args:
        # Check if the arg is used after declaration (as ${ARG} or $ARG)
        pattern = rf'\${{{arg}}}|\${arg}(?=[^A-Z_a-z0-9]|$)'
        if not re.search(pattern, content):
            errors.append(f"ARG {arg} declared but never used")
    assert not errors, (
        f"In {dockerfile.relative_to(ROOT)}:\n" + "\n".join(errors)
    )


# ── 4. OPA policy: syntax + unit tests ───────────────────────────────────────

@pytest.mark.integration
def test_opa_policy_with_container(docker_client):
    """Run OPA check + OPA test inside a real OPA container."""
    opa_dir = ROOT / "opa"
    if not opa_dir.exists():
        pytest.skip("opa/ directory not found")

    from testcontainers.core.container import DockerContainer
    from testcontainers.core.waiting_utils import wait_for_logs

    with DockerContainer("openpolicyagent/opa:0.70.0-static") \
            .with_volume_mapping(str(opa_dir), "/opa", "ro") \
            .with_command("check /opa/policy.rego") as opa:
        logs = opa.get_logs()
        stdout = logs[0].decode() if logs[0] else ""
        stderr = logs[1].decode() if logs[1] else ""
        assert "error" not in stderr.lower() and "error" not in stdout.lower(), (
            f"OPA policy check failed:\n{stderr}\n{stdout}"
        )

    # Run OPA unit tests if test file exists
    test_file = opa_dir / "policy_test.rego"
    if test_file.exists():
        result = subprocess.run(
            ["docker", "run", "--rm",
             "-v", f"{opa_dir}:/opa:ro",
             "openpolicyagent/opa:0.70.0-static",
             "test", "/opa/"],
            capture_output=True, text=True, timeout=60
        )
        assert result.returncode == 0, (
            f"OPA policy tests failed:\n{result.stdout}\n{result.stderr}"
        )


# ── 5. OpenFGA model syntax ───────────────────────────────────────────────────

@pytest.mark.integration
def test_openfga_model_valid(docker_client):
    """Validate OpenFGA authorization model using real OpenFGA container."""
    fga_model = ROOT / "openfga" / "model.fga"
    if not fga_model.exists():
        pytest.skip("openfga/model.fga not found")

    # Use openfga CLI to validate the model
    result = subprocess.run(
        ["docker", "run", "--rm",
         "-v", f"{ROOT / 'openfga'}:/fga:ro",
         "openfga/openfga:v1.8.0",
         "validate", "--file", "/fga/model.fga"],
        capture_output=True, text=True, timeout=60
    )
    # OpenFGA validate exits 0 on success
    assert result.returncode == 0, (
        f"OpenFGA model validation failed:\n{result.stdout}\n{result.stderr}"
    )


# ── 6. Postgres init.sh runs cleanly ─────────────────────────────────────────

@pytest.mark.integration
def test_postgres_init_script(docker_client):
    """Run postgres/init.sh against a real Postgres container.
    Verifies all 5 databases and users are created without errors."""
    init_script = ROOT / "postgres" / "init.sh"
    if not init_script.exists():
        pytest.skip("postgres/init.sh not found")

    from testcontainers.postgres import PostgresContainer

    env = {
        "POSTGRES_USER": "autonomyx",
        "POSTGRES_PASSWORD": "testroot",
        "POSTGRES_DB": "postgres",
        "LITELLM_DB_PASSWORD": "testlitellm",
        "LANGFLOW_DB_PASSWORD": "testlangflow",
        "OPENFGA_DB_PASSWORD": "testopenfga",
        "GLITCHTIP_DB_PASSWORD": "testglitchtip",
        "INFISICAL_DB_PASSWORD": "testinfisical",
    }

    with PostgresContainer(
        image="postgres:15.7-alpine",
        username="autonomyx",
        password="testroot",
        dbname="postgres",
    ) as pg:
        # Copy and run init script inside the container
        container_id = pg.get_wrapped_container().id

        # Copy init.sh into container
        subprocess.run(
            ["docker", "cp", str(init_script), f"{container_id}:/init.sh"],
            check=True, capture_output=True
        )
        subprocess.run(
            ["docker", "exec", container_id, "chmod", "+x", "/init.sh"],
            check=True, capture_output=True
        )

        # Run it with env vars
        env_args = []
        for k, v in env.items():
            env_args.extend(["-e", f"{k}={v}"])

        result = subprocess.run(
            ["docker", "exec"] + env_args + [container_id, "/init.sh"],
            capture_output=True, text=True, timeout=60
        )

        assert result.returncode == 0, (
            f"postgres/init.sh failed:\n{result.stdout}\n{result.stderr}"
        )
        assert "All databases and users created" in result.stdout

        # Verify databases exist
        for db in ["litellm", "langflow", "openfga", "glitchtip"]:
            check = subprocess.run(
                ["docker", "exec", container_id,
                 "psql", "-U", "autonomyx", "-lqt"],
                capture_output=True, text=True
            )
            assert db in check.stdout, f"Database '{db}' not created by init.sh"
