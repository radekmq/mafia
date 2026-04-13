from characters.character import Ability, Character, RoleType
from game_state import GameState


def ability_effect_night_minion(game_state: GameState):
    """Effect of the Bibliotekarka's ability."""


def ability_callback(game_state: GameState, data: dict):
    """Handle callback for the Bibliotekarka's ability."""


def ability_setup(game_state: GameState):
    """Configure for the Bibliotekarka's ability."""


def on_night_exit(game_state: GameState):
    """Handle actions to perform when the night phase ends for the Bibliotekarka."""


char_ability = Ability(
    description=(
        "Na początku wiesz, że 1 z 2 graczy jest konkretnym Outsiderem "
        "(lub że żaden nie jest w grze). Bibliotekarka dowiaduje się, "
        "że konkretny Outsider jest w grze, ale nie kto go gra."
    ),
    effect_night_minion=ability_effect_night_minion,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)


class BibliotekarkaCharacter(Character):
    """Class representing the Bibliotekarka character."""

    def __init__(self):
        """Initialize the Bibliotekarka character."""

        super().__init__(
            name="Bibliotekarka",
            role_type=RoleType.TOWNSFOLK,
            ability=char_ability,
            image_path="bibliotekarka.png",
            route="bibliotekarka",
        )
