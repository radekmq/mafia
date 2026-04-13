from characters.character import Ability, Character, RoleType
from game_state import GameState


def ability_effect_night_minion(game_state: GameState):
    """Effect of the Empata's ability."""


def ability_callback(game_state: GameState, data: dict):
    """Handle callback for the Empata's ability."""


def ability_setup(game_state: GameState):
    """Configure for the Empata's ability."""


def on_night_exit(game_state: GameState):
    """Handle actions to perform when the night phase ends for the Empata."""


char_ability = Ability(
    description=(
        "Po każdej nocy Empata dowiaduje się, ilu z jego dwóch "
        "żyjących sąsiadów jest złych. Empata uczy się, "
        "czy sąsiadujący z nim gracze są dobrzy czy źli."
    ),
    effect_night_minion=ability_effect_night_minion,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)


class EmpataCharacter(Character):
    """Class representing the Empata character."""

    def __init__(self):
        """Initialize the Empata character."""

        super().__init__(
            name="Empata",
            role_type=RoleType.TOWNSFOLK,
            ability=char_ability,
            image_path="empata.png",
            route="empata",
        )
