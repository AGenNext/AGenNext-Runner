#!/usr/bin/env python3
"""scripts/gen_ci_env.py
Generates .env.ci with type-aware placeholder values for all keys in .env.example.
Used by CI to run docker compose config --quiet without real secrets.
Docker Compose validates certain field types (mem_limit, ports, etc.) so
placeholders must be type-correct.
"""
import pathlib, sys

root = pathlib.Path(__file__).parent.parent
example = root / ".env.example"
output  = root / ".env.ci"

if not example.exists():
    print(f"❌ {example} not found")
    sys.exit(1)

# Keys whose values must be memory size strings (e.g. 512m, 8g)
MEM_KEYS = {"MEM_LIMIT", "MEMSWAP_LIMIT", "MEM_SWAP", "MEMORY_LIMIT", "MEMORY"}

# Keys whose values must be integers
INT_KEYS = {"PORT", "TIMEOUT", "INTERVAL", "RETRIES", "SIZE",
            "COUNT", "LIMIT", "MAX", "MIN", "WORKERS", "REPLICAS"}

lines = []
for line in example.read_text().splitlines():
    if line.startswith("#") or "=" not in line:
        lines.append(line)
        continue
    key = line.split("=")[0].strip()
    key_upper = key.upper()
    # Check if any mem/int keyword appears in the key name
    if any(m in key_upper for m in MEM_KEYS):
        # Skip — let docker-compose use its own default (e.g. ${VAR:-76g})
        # Setting ci_placeholder overrides the default and breaks validation
        lines.append(f"# {key}= (skipped — compose has typed default)")
    elif any(m in key_upper for m in INT_KEYS):
        lines.append(f"{key}=0")
    else:
        lines.append(f"{key}=ci_placeholder")

output.write_text("\n".join(lines))
count = sum(1 for l in lines if "=" in l and not l.startswith("#"))
print(f"✅ Generated {output} ({count} vars)")
