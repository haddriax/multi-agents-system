from pydantic import BaseModel, Field
from src.system.models.perception import Perception, CellContent
from src.system.models.action import Action
from src.system.entities.objects.waste import Waste


class Knowledge(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    position: tuple[int, int]
    carried_wastes: list[Waste] = Field(default_factory=list)

    belief_map: dict[tuple[int, int], CellContent] = Field(default_factory=dict)
    """ Belief_map is memory based on last perceptions, but not ground truth! """

    # Transient knowledge
    last_perception: Perception | None = None
    last_action:     Action | None = None

    # Bot behavior
    planned_path: list[tuple[int, int]] = Field(default_factory=list)
    """ Path built by the Pathfinder, based on the bot's beliefs """

    current_goal: tuple[int, int] | None = None
    """ The target cell the bot is heading to. Used to detect if the waste disappeared. """
