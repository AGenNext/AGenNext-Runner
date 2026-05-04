import importlib, sys
from pathlib import Path


def load_entrypoint(entrypoint: str, project_dir: str = "."):
    p = str(Path(project_dir).resolve())
    if p not in sys.path:
        sys.path.insert(0, p)
    mod, attr = entrypoint.split(":", 1)
    m = importlib.import_module(mod)
    return getattr(m, attr)
