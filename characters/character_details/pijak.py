from characters.character import Ability, Character, RoleType
from game_state import GameState


def ability_effect_night_minion(game_state: GameState):
    """Effect of the Pijak's ability."""


def ability_callback(game_state: GameState, data: dict):
    """Handle callback for the Pijak's ability."""


def ability_setup(game_state: GameState):
    """Configure for the Pijak's ability."""


def on_night_exit(game_state: GameState):
    """Handle actions to perform when the night phase ends for the Pijak."""


char_ability = Ability(
    description=(
        "Nie wiesz, że jesteś Pijakiem. Myślisz, że jesteś "
        "postacią z grupy Townsfolk, ale nią nie jesteś."
    ),
    effect_night_minion=ability_effect_night_minion,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)


class PijakCharacter(Character):
    """Class representing the Pijak character."""

    def __init__(self):
        """Initialize the Pijak character."""

        super().__init__(
            name="Pijak",
            role_type=RoleType.OUTSIDER,
            ability=char_ability,
            image_path="pijak.png",
            route="pijak",
        )
