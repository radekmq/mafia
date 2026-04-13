from characters.character import Ability, Character, RoleType
from game_state import GameState


def ability_effect_night_minion(game_state: GameState):
    """Effect of the Truciciel's ability."""


def ability_callback(game_state: GameState, data: dict):
    """Handle callback for the Truciciel's ability."""


def ability_setup(game_state: GameState):
    """Configure for the Truciciel's ability."""


def on_night_exit(game_state: GameState):
    """Handle actions to perform when the night phase ends for the Truciciel."""


char_ability = Ability(
    description=(
        "Każdej nocy wybierz gracza: tej nocy i następnego dnia "
        "ten gracz jest zatruty. Truciciel potajemnie zakłóca "
        "działanie zdolności postaci."
    ),
    effect_night_minion=ability_effect_night_minion,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)


class TrucicielCharacter(Character):
    """Class representing the Truciciel character."""

    def __init__(self):
        """Initialize the Truciciel character."""

        super().__init__(
            name="Truciciel",
            role_type=RoleType.MINION,
            ability=char_ability,
            image_path="truciciel.png",
            route="truciciel",
        )
