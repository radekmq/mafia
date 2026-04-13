from characters.character import Ability, Character, RoleType
from game_state import GameState


def ability_effect_night_minion(game_state: GameState):
    """Effect of the Zabójca's ability."""


def ability_callback(game_state: GameState, data: dict):
    """Handle callback for the Zabójca's ability."""


def ability_setup(game_state: GameState):
    """Configure for the Zabójca's ability."""


def on_night_exit(game_state: GameState):
    """Handle actions to perform when the night phase ends for the Zabójca."""


char_ability = Ability(
    description=(
        "Raz na grę, w ciągu dnia, publicznie wybierz gracza: jeśli jest Demonem, ginie. "
        "Zabójca (Slayer) może zabić Demona, jeśli odgadnie, kim on jest."
    ),
    effect_night_minion=ability_effect_night_minion,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)


class ZabojcaCharacter(Character):
    """Class representing the Zabójca character."""

    def __init__(self):
        """Initialize the Zabójca character."""

        super().__init__(
            name="Zabojca",
            role_type=RoleType.TOWNSFOLK,
            ability=char_ability,
            image_path="zabojca.png",
            route="zabojca",
        )
