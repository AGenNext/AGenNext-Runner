import pytest
from pathlib import Path

# ── Strict duplicate key validation ──────────────────────────────────────────
import yaml
from yaml.constructor import SafeConstructor
from yaml.resolver import Resolver
from yaml.composer import Composer
from yaml.reader import Reader
from yaml.scanner import Scanner
from yaml.parser import Parser

class StrictConstructor(SafeConstructor):
    def construct_mapping(self, node, deep=False):
        if not isinstance(node, yaml.MappingNode):
            raise yaml.constructor.ConstructorError(
                None, None, f"expected mapping, got {node.id}", node.start_mark)
        keys_seen = {}
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in keys_seen:
                raise yaml.constructor.ConstructorError(
                    "while constructing mapping", node.start_mark,
                    f"duplicate key '{key}' (first seen at line {keys_seen[key]+1})",
                    key_node.start_mark)
            keys_seen[key] = key_node.start_mark.line
        return super().construct_mapping(node, deep=deep)

class StrictLoader(Reader, Scanner, Parser, Composer, StrictConstructor, Resolver):
    def __init__(self, stream):
        Reader.__init__(self, stream); Scanner.__init__(self)
        Parser.__init__(self); Composer.__init__(self)
        StrictConstructor.__init__(self); Resolver.__init__(self)

def strict_load(path):
    with open(path) as f:
        return yaml.load(f, Loader=StrictLoader)

@pytest.mark.parametrize("compose_file", [
    "docker-compose.yml",
    "docker-compose.business.yml",
])
def test_no_duplicate_keys(compose_file):
    """Catches duplicate YAML keys that yaml.safe_load() silently ignores."""
    root = Path(__file__).parent.parent
    path = root / compose_file
    if not path.exists():
        pytest.skip(f"{compose_file} not found")
    try:
        strict_load(str(path))
    except yaml.constructor.ConstructorError as e:
        pytest.fail(f"Duplicate key in {compose_file}: {e}")


# ── Docker Compose schema + structural validation ─────────────────────────────
import subprocess
import shutil

@pytest.mark.parametrize("compose_file", [
    "docker-compose.yml",
    "docker-compose.business.yml",
])
def test_compose_config_valid(compose_file):
    """Runs 'docker compose config --quiet' — catches schema + structural errors
    that PyYAML parsing alone misses (duplicate keys, bad references, etc.).
    Skipped automatically if Docker is not installed (e.g. in CI lint jobs)."""
    if not shutil.which("docker"):
        pytest.skip("docker not installed — skipping compose validation")

    # Check docker compose is functional (not a stub/mock)
    check = subprocess.run(
        ["docker", "compose", "version"],
        capture_output=True, text=True
    )
    if check.returncode != 0 or "version" not in check.stdout.lower():
        pytest.skip("docker compose not functional — skipping compose validation")

    root = Path(__file__).parent.parent
    path = root / compose_file
    if not path.exists():
        pytest.skip(f"{compose_file} not found")

    # Generate type-aware .env.ci using the shared script
    subprocess.run(
        ["python3", "scripts/gen_ci_env.py"],
        check=True, capture_output=True, cwd=str(root)
    )
    env_file = root / ".env.ci"

    result = subprocess.run(
        ["docker", "compose",
         "-f", str(path),
         "--env-file", str(env_file),
         "config", "--quiet"],
        capture_output=True, text=True, cwd=str(root)
    )

    if result.returncode != 0:
        pytest.fail(
            f"docker compose config --quiet failed for {compose_file}:\n"
            f"{result.stderr.strip()}"
        )


# ── GitHub Actions workflow validation ────────────────────────────────────────
import glob

# Known invalid inputs per action (subset — the ones that have bitten us)
INVALID_INPUTS = {
    "docker/build-push-action": {"dockerfile"},   # correct param is 'file'
    "docker/setup-buildx-action": {"dockerfile"},
}

# Known valid cache types
VALID_CACHE_TYPES = {"registry", "local", "gha", "s3", "azblob", "inline"}

def get_workflow_files():
    root = Path(__file__).parent.parent
    return list((root / ".github" / "workflows").glob("*.yml"))

@pytest.mark.parametrize("workflow_file", get_workflow_files())
def test_workflow_no_invalid_action_inputs(workflow_file):
    """Catches invalid inputs to known GitHub Actions (e.g. dockerfile in build-push-action)."""
    import yaml as _yaml
    data = _yaml.safe_load(workflow_file.read_text())
    if not data or 'jobs' not in data:
        return

    errors = []
    for job_name, job in (data.get('jobs') or {}).items():
        for step in (job.get('steps') or []):
            uses = step.get('uses', '')
            action = uses.split('@')[0] if '@' in uses else ''
            with_inputs = set((step.get('with') or {}).keys())

            for known_action, bad_inputs in INVALID_INPUTS.items():
                if known_action in action:
                    found_bad = with_inputs & bad_inputs
                    if found_bad:
                        errors.append(
                            f"Job '{job_name}' step '{step.get('name', uses)}': "
                            f"invalid input(s) {found_bad} for {action}"
                        )

    if errors:
        pytest.fail("\n".join(errors))


@pytest.mark.parametrize("workflow_file", get_workflow_files())
def test_workflow_valid_yaml(workflow_file):
    """Ensures every workflow file is valid YAML with no duplicate keys."""
    try:
        strict_load(str(workflow_file))
    except Exception as e:
        pytest.fail(f"Invalid YAML in {workflow_file.name}: {e}")
