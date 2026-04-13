from characters.character import Ability, Character, RoleType
from game_state import GameState


def ability_effect_night_minion(game_state: GameState):
    """Effect of the Święty's ability."""


def ability_callback(game_state: GameState, data: dict):
    """Handle callback for the Święty's ability."""


def ability_setup(game_state: GameState):
    """Configure for the Święty's ability."""


def on_night_exit(game_state: GameState):
    """Handle actions to perform when the night phase ends for the Święty."""


char_ability = Ability(
    description=(
        "Jeśli zostaniesz stracony w wyniku egzekucji, twoja drużyna przegrywa. "
        "Święty (Saint) kończy grę porażką swojej drużyny, jeśli zostanie stracony."
    ),
    effect_night_minion=ability_effect_night_minion,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)


class SwietyCharacter(Character):
    """Class representing the Święty character."""

    def __init__(self):
        """Initialize the Święty character."""

        super().__init__(
            name="Święty",
            role_type=RoleType.OUTSIDER,
            ability=char_ability,
            image_path="swiety.png",
            route="swiety",
        )
