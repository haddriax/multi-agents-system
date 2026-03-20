import yaml

def load_config(config_path: str = None) -> dict:
    if config_path is None:
        config_path = '../config.yaml'

    c: dict
    with open(config_path, 'r') as f:
        c = yaml.safe_load(f)

    return c

if __name__ == '__main__':
    config: dict = load_config()
    print(config)