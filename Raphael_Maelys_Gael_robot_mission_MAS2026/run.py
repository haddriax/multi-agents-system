# Group: 9
# Date: 20-03-2026
# Members: Maëlys Hanoire, Raphaël Vignal, Gaël Garnier

import yaml

from Raphael_Maelys_Gael_robot_mission_MAS2026.system.config import Config
from Raphael_Maelys_Gael_robot_mission_MAS2026.system.system_model import SystemModel

def load_config(config_path: str = None) -> Config:
    if config_path is None:
        config_path = 'config.yaml'

    config: Config
    try:
        config = Config.from_yaml(config_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: {config_path}")
    except yaml.YAMLError as exc:
        raise exc

    return config

def init_world():
    config: Config = load_config()

    model = SystemModel(config)
    print(f"\nModel created with grid size: {model.grid.width}x{model.grid.height}")

    robot_agents = [a for a in model.agents if hasattr(a, 'deliberate')]
    print(f"Number of robot agents: {len(robot_agents)}")

    return model, robot_agents, config.simulation.steps

if __name__ == '__main__':
    import os
    import subprocess
    import sys

    _PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _APP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "viewer", "app.py")

    subprocess.run(
        [sys.executable, "-m", "solara", "run", _APP_PATH] + sys.argv[1:],
        cwd=_PROJECT_ROOT,
        check=True,
    )