"""
Solara entry point for the multi-agent radioactive waste visualisation.

Preferred:  solara run src/viewer/app.py
Also works: python src/viewer/app.py [--host HOST] [--port PORT]
"""
import os

from src.system.config import Config
from src.viewer.visualization import create_visualization

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

config = Config.from_yaml(os.path.join(_PROJECT_ROOT, "config.yaml"))
page   = create_visualization(config)

if __name__ == "__main__" and not os.environ.get("_SOLARA_LAUNCHED"):
    import subprocess
    import sys

    env = os.environ.copy()
    env["_SOLARA_LAUNCHED"] = "1"

    subprocess.run(
        [sys.executable, "-m", "solara", "run", os.path.abspath(__file__)] + sys.argv[1:],
        cwd=_PROJECT_ROOT,
        env=env,
    )
