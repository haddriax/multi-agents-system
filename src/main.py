import yaml

from src.system.config import Config
from src.system.system_model import SystemModel

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
    model, robot_agents, nb_steps = init_world()

    for agent in robot_agents:
        print(f"  {agent.__class__.__name__} at position {agent.pos}")

    model.step()

    # @todo some validation logic early on could be great?
    for agent in robot_agents:
        print(f"\nAnalysis of {agent.__class__.__name__}:")
        print(f"  Actual position: {agent.pos}")
        print(f"  Position in knowledge: {agent.knowledge.position}")
        print(f"  Last action: {agent.knowledge.last_action}")
        print(f"  Perception readings count: {len(agent.knowledge.last_perception.readings)}")
        print(f"  Belief map entries: {len(agent.knowledge.belief_map)}")

    for i in range(nb_steps):
        model.step()
        print(f"Step {i} done.")