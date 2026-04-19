"""
Solara visualisation module for the multi-agent radioactive waste simulation.

Entry point: python -m src.main [--host HOST] [--port PORT]
"""
import os

from src.system.config import Config
from src.viewer.visualization import create_visualization

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

config = Config.from_yaml(os.path.join(_PROJECT_ROOT, "config.yaml"))
page   = create_visualization(config)

