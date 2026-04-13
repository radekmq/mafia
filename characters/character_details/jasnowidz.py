from characters.character import Ability, Character, RoleType
from game_state import GameState


def ability_effect_night_minion(game_state: GameState):
    """Effect of the Jasnowidz's ability."""


def ability_callback(game_state: GameState, data: dict):
    """Handle callback for the Jasnowidz's ability."""


def ability_setup(game_state: GameState):
    """Configure for the Jasnowidz's ability."""


def on_night_exit(game_state: GameState):
    """Handle actions to perform when the night phase ends for the Jasnowidz."""


char_ability = Ability(
    description=(
        "Po każdej nocy wybierz 2 graczy: dowiadujesz się, "
        "czy którykolwiek z nich jest Demonem. Jasnowidz dowiaduje się, "
        "czy którykolwiek z dwóch graczy jest Demonem."
    ),
    effect_night_minion=ability_effect_night_minion,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)


class JasnowidzCharacter(Character):
    """Class representing the Jasnowidz character."""

    def __init__(self):
        """Initialize the Jasnowidz character."""

        super().__init__(
            name="Jasnowidz",
            role_type=RoleType.TOWNSFOLK,
            ability=char_ability,
            image_path="jasnowidz.png",
            route="jasnowidz",
        )
