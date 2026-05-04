from pathlib import Path
import yaml


def load_agentnext_config(project_dir: str = ".") -> dict:
    cfg_path = Path(project_dir) / "agentnext.yaml"
    if not cfg_path.exists():
        raise FileNotFoundError("agentnext.yaml not found")
    data = yaml.safe_load(cfg_path.read_text())
    if not isinstance(data, dict) or "agent" not in data:
        raise ValueError("invalid agentnext.yaml")
    return data


def validate_config_shape(cfg: dict) -> None:
    required = ["agent", "runtime", "authorization", "identity", "tools"]
    for key in required:
        if key not in cfg:
            raise ValueError(f"missing config section: {key}")
