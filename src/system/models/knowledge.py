from pydantic import BaseModel, Field
from perception import Perception, CellContent
from src.system.models.action import ActionType
from src.system.models.types import WasteType


class Knowledge(BaseModel):
    position: tuple[int, int]
    carried_wastes: list[WasteType] = Field(default_factory=list)

    belief_map: dict[tuple[int, int], CellContent] = Field(default_factory=dict)
    """ Belief_map is memory based on last perceptions, but not grouf fact! """

    # Transient knowledge
    last_perception: Perception | None = None
    last_action:     ActionType | None = None