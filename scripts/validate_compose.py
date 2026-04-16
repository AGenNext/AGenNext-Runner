#!/usr/bin/env python3
"""
Strict docker-compose.yml validator.
Catches duplicate keys that yaml.safe_load() silently ignores.
Run: python3 scripts/validate_compose.py
"""
import sys
import subprocess

class DuplicateKeyLoader:
    """YAML loader that raises on duplicate keys at any nesting level."""
    def __init__(self):
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
                        None, None,
                        f"expected a mapping node, got {node.id}",
                        node.start_mark
                    )
                keys_seen = {}
                for key_node, _ in node.value:
                    key = self.construct_object(key_node, deep=deep)
                    if key in keys_seen:
                        raise yaml.constructor.ConstructorError(
                            "while constructing a mapping", node.start_mark,
                            f"found duplicate key: '{key}' (first at line {keys_seen[key]+1})",
                            key_node.start_mark
                        )
                    keys_seen[key] = key_node.start_mark.line
                return super().construct_mapping(node, deep=deep)

        class StrictLoader(Reader, Scanner, Parser, Composer, StrictConstructor, Resolver):
            def __init__(self, stream):
                Reader.__init__(self, stream)
                Scanner.__init__(self)
                Parser.__init__(self)
                Composer.__init__(self)
                StrictConstructor.__init__(self)
                Resolver.__init__(self)

        self.loader = StrictLoader

    def load(self, stream):
        import yaml
        return yaml.load(stream, Loader=self.loader)


def validate(path):
    print(f"Validating {path}...")
    loader = DuplicateKeyLoader()
    try:
        with open(path) as f:
            loader.load(f)
        print(f"  ✅ No duplicate keys")
    except Exception as e:
        print(f"  ❌ {e}")
        return False

    # Also run docker compose config if available
    try:
        result = subprocess.run(
            ["docker", "compose", "config", "--quiet"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"  ❌ docker compose config: {result.stderr.strip()}")
            return False
        print(f"  ✅ docker compose config passed")
    except FileNotFoundError:
        print(f"  ⏭  docker not available — skipping compose config check")

    return True


if __name__ == "__main__":
    files = sys.argv[1:] or ["docker-compose.yml", "docker-compose.business.yml"]
    failed = []
    for f in files:
        if not validate(f):
            failed.append(f)
    if failed:
        print(f"\n❌ Failed: {failed}")
        sys.exit(1)
    print("\n✅ All files valid")
