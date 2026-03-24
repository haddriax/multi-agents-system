from pydantic import BaseModel, Field
from src.system.models.perception import Perception, CellContent
from src.system.models.action import ActionType
from src.system.models.types import WasteType


class Knowledge(BaseModel):
    position: tuple[int, int]
    carried_wastes: list[WasteType] = Field(default_factory=list)

    belief_map: dict[tuple[int, int], CellContent] = Field(default_factory=dict)
    """ Belief_map is memory based on last perceptions, but not ground truth! """

    # Transient knowledge
    last_perception: Perception | None = None
    last_action:     ActionType | None = None

    # Bot behavior
    planned_path: list[tuple[int, int]] = []
    """ Path build by the Pathfinder, based on the bot belief """

    current_goal: tuple[int, int] | None = None
    """ The target cell when the bot must go. Use it for goal comparison, like 'did the waste here disappeared?' """