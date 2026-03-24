from dataclasses import dataclass, field
import yaml


@dataclass(frozen=True)
class SimulationConfig:
    steps:     int
    step_jump: int = 1


@dataclass(frozen=True)
class GridConfig:
    width:  int
    height: int


@dataclass(frozen=True)
class SpawningConfig:
    n_green:        int
    n_yellow:       int
    n_red:          int
    n_waste_green:  int
    n_waste_yellow: int
    n_waste_red:    int


@dataclass(frozen=True)
class ViewerConfig:
    # Agent colors
    waste_color_green:  str = "#00aa00"
    waste_color_yellow: str = "#ccaa00"
    waste_color_red:    str = "#cc2200"
    robot_color_green:  str = "limegreen"
    robot_color_yellow: str = "gold"
    robot_color_red:    str = "tomato"

    # Zone background colors
    zone_color_z1: str = "lightgreen"
    zone_color_z2: str = "lightyellow"
    zone_color_z3: str = "lightcoral"

    # Other elements
    disposal_zone_color: str = "purple"

    # Play speed
    play_interval: float = 0.4


@dataclass(frozen=True)
class Config:
    simulation: SimulationConfig
    grid:       GridConfig
    spawning:   SpawningConfig
    viewer:     ViewerConfig = field(default_factory=ViewerConfig)

    @classmethod
    def from_yaml(cls, path: str) -> "Config":
        with open(path, "r") as f:
            raw = yaml.safe_load(f)

        return cls(
            simulation = SimulationConfig(**raw["simulation"]),
            grid       = GridConfig(**raw["grid"]),
            spawning   = SpawningConfig(**raw["spawning"]),
            viewer     = ViewerConfig(**raw.get("viewer", {})),
        )