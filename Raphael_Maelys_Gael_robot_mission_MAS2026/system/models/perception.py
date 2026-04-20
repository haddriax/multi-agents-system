# Group: 9
# Date: 20-03-2026
# Members: Maëlys Hanoire, Raphaël Vignal, Gaël Garnier

from pydantic.dataclasses import dataclass
from pydantic import Field

from Raphael_Maelys_Gael_robot_mission_MAS2026.system.models.types import WasteType, RobotType, MAX_WASTE_PER_CELL


@dataclass(frozen=True)
class CellContent:
    """ The percetion of a cell from a bot perspective"""
    # Cell static state
    radioactivity_value: float = Field(ge=0.0, le=1.0)

    # Cell dynamic state
    waste_type: WasteType = Field(default=WasteType.NONE)
    waste_quantity: int = Field(default=0, ge=0, le=MAX_WASTE_PER_CELL)
    robot_type: RobotType = Field(default=RobotType.NONE)
    has_disposal_zone: bool = False

    @property
    def get_zone(self) -> int:
        """
        Return the zone number, based on the radioactivity value.
        We can read that as a risk score.
        1: green, 2: yellow, 3: red
        """
        if self.radioactivity_value <= 0.33:
            return 1
        elif self.radioactivity_value <= 0.66:
            return 2
        else:
            return 3

    def has_waste(self) -> bool:
        return self.waste_quantity > 0
    

@dataclass(frozen=True)
class Perception:

    perceiver_position: tuple[int, int]
    """
    The position of the agent perceiving.
    """

    readings: tuple[tuple[tuple[int, int], CellContent], ...]
    """ 
    The collection of what the bot sees (all cells).
    Note that the coordinates are centered on the agent that perceives!!!
    """

    step: int = Field(ge=0)
    """
    The step when this perception is created.
    """

    perceiver_id: int = Field(ge=0)

    foreign_reservations: frozenset[tuple[int, int]] = Field(default_factory=frozenset)
    """
    Positions within perception range that are currently reserved by other bots.
    It's a blacklist.
    """