from characters.character import Ability, Character, RoleType
from game_state import GameState


def ability_effect_night_minion(game_state: GameState):
    """Effect of the Grabarz's ability."""


def ability_callback(game_state: GameState, data: dict):
    """Handle callback for the Grabarz's ability."""


def ability_setup(game_state: GameState):
    """Configure for the Grabarz's ability."""


def on_night_exit(game_state: GameState):
    """Handle actions to perform when the night phase ends for the Grabarz."""


char_ability = Ability(
    description="Każdej nocy dowiadujesz się, jaka postać została dziś stracona."
    "Grabarz dowiaduje się kogo stracono w ciągu dnia.",
    effect_night_minion=ability_effect_night_minion,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)


class GrabarzCharacter(Character):
    """Class representing the Grabarz character."""

    def __init__(self):
        """Initialize the Grabarz character."""

        super().__init__(
            name="Grabarz",
            role_type=RoleType.TOWNSFOLK,
            ability=char_ability,
            image_path="grabarz.png",
            route="grabarz",
        )
