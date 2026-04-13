from characters.character import Ability, Character, RoleType
from game_state import GameState


def ability_effect_night_minion(game_state: GameState):
    """Effect of the Kucharz's ability."""


def ability_callback(game_state: GameState, data: dict):
    """Handle callback for the Kucharz's ability."""


def ability_setup(game_state: GameState):
    """Configure for the Kucharz's ability."""


def on_night_exit(game_state: GameState):
    """Handle actions to perform when the night phase ends for the Kucharz."""


char_ability = Ability(
    description=(
        "Na początku wiesz, ile par złych graczy siedzi obok siebie. "
        "Kucharz wie, czy źli gracze siedzą obok siebie."
    ),
    effect_night_minion=ability_effect_night_minion,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)


class KucharzCharacter(Character):
    """Class representing the Kucharz character."""

    def __init__(self):
        """Initialize the Kucharz character."""

        super().__init__(
            name="Kucharz",
            role_type=RoleType.TOWNSFOLK,
            ability=char_ability,
            image_path="kucharz.png",
            route="kucharz",
        )
