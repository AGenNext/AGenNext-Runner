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
