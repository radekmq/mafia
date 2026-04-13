from characters.character import Ability, Character, RoleType
from game_state import GameState


def ability_effect_night_minion(game_state: GameState):
    """Effect of the Praczka's ability."""


def ability_callback(game_state: GameState, data: dict):
    """Handle callback for the Praczka's ability."""


def ability_setup(game_state: GameState):
    """Configure for the Praczka's ability."""


def on_night_exit(game_state: GameState):
    """Handle actions to perform when the night phase ends for the Praczka."""


char_ability = Ability(
    description=(
        "Zaczynasz grę wiedząc, że 1 z 2 graczy jest konkretną postacią Mieszczanina."
        "Praczka dowiaduje się, że dana postać Mieszczanina jest w grze, "
        "ale nie wie, który gracz ją posiada."
    ),
    effect_night_minion=ability_effect_night_minion,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)


class PraczkaCharacter(Character):
    """Class representing the Praczka character."""

    def __init__(self):
        """Initialize the Praczka character."""

        super().__init__(
            name="Praczka",
            role_type=RoleType.TOWNSFOLK,
            ability=char_ability,
            image_path="praczka.png",
            route="praczka",
        )
