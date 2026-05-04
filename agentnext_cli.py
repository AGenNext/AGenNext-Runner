import argparse
import os
import shutil
import tarfile
from pathlib import Path
import yaml

from runner.harness.config_loader import load_agentnext_config, validate_config_shape
from runner.harness.scenarios import invoke_local

TEMPLATE_DIR = Path(__file__).parent / "templates" / "langgraph-deepagent"


def _slug(name: str) -> str:
    return name.replace("-", "_")


def cmd_init(args):
    if args.template != "langgraph-deepagent":
        raise SystemExit("unsupported template")
    project = Path(args.name)
    project.mkdir(parents=True, exist_ok=True)
    for p in TEMPLATE_DIR.rglob("*"):
        if p.is_dir():
            continue
        rel = p.relative_to(TEMPLATE_DIR)
        out = project / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        text = p.read_text()
        text = text.replace("{{AGENT_ID}}", _slug(args.name)).replace("{{AGENT_NAME}}", args.name.replace("-", " ").title())
        out.write_text(text)
    print(f"Initialized {project}")


def cmd_dev(args):
    cfg = load_agentnext_config(".")
    validate_config_shape(cfg)
    print("AgentNext dev harness ready")
    print(f"tenant_id=local_dev actor=agent:{cfg['agent']['id']} auth_mode=managed kernel=stub")
    print('Run: agentnext invoke "hello"')


def cmd_invoke(args):
    result = invoke_local(args.message, project_dir=".")
    print(result)


def cmd_package(args):
    cfg = load_agentnext_config(".")
    validate_config_shape(cfg)
    required = ["agent.py", "tools.py", "agentnext.yaml", "requirements.txt", "README.md"]
    missing = [f for f in required if not Path(f).exists()]
    if missing:
        raise SystemExit(f"missing required files: {missing}")
    dist = Path(".agentnext") / "dist"
    dist.mkdir(parents=True, exist_ok=True)
    artifact = dist / f"{cfg['agent']['id']}.tar.gz"
    with tarfile.open(artifact, "w:gz") as tar:
        for path in required:
            tar.add(path)
        for py in Path(".").glob("*.py"):
            tar.add(py)
    print(str(artifact))


def main():
    parser = argparse.ArgumentParser(prog="agentnext")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init")
    p_init.add_argument("name")
    p_init.add_argument("--template", default="langgraph-deepagent")
    p_init.set_defaults(func=cmd_init)

    p_dev = sub.add_parser("dev")
    p_dev.set_defaults(func=cmd_dev)

    p_inv = sub.add_parser("invoke")
    p_inv.add_argument("message")
    p_inv.set_defaults(func=cmd_invoke)

    p_pkg = sub.add_parser("package")
    p_pkg.set_defaults(func=cmd_package)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
