from dataclasses import dataclass
import yaml


@dataclass(frozen=True)
class SimulationConfig:
    steps: int


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
class Config:
    simulation: SimulationConfig
    grid:       GridConfig
    spawning:   SpawningConfig

    @classmethod
    def from_yaml(cls, path: str) -> "Config":
        with open(path, "r") as f:
            raw = yaml.safe_load(f)

        return cls(
            simulation = SimulationConfig(**raw["simulation"]),
            grid       = GridConfig(**raw["grid"]),
            spawning   = SpawningConfig(**raw["spawning"]),
        )