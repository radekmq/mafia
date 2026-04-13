from characters.character import Ability, Character, RoleType
from game_state import GameState


def ability_effect_night_minion(game_state: GameState):
    """Effect of the Dziewica's ability."""


def ability_callback(game_state: GameState, data: dict):
    """Handle callback for the Dziewica's ability."""


def ability_setup(game_state: GameState):
    """Configure for the Dziewica's ability."""


def on_night_exit(game_state: GameState):
    """Handle actions to perform when the night phase ends for the Dziewica."""


char_ability = Ability(
    description=(
        "Za pierwszym razem, gdy zostaniesz nominowany, jeśli nominujący jest Mieszczaninem, "
        "zostaje natychmiast stracony."
        "Dziewica może nieświadomie doprowadzić do egzekucji swojego oskarżyciela, "
        "jednocześnie potwierdzając, którzy gracze są Mieszczanami."
    ),
    effect_night_minion=ability_effect_night_minion,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)


class DziewicaCharacter(Character):
    """Class representing the Dziewica character."""

    def __init__(self):
        """Initialize the Dziewica character."""

        super().__init__(
            name="Dziewica",
            role_type=RoleType.TOWNSFOLK,
            ability=char_ability,
            image_path="dziewica.png",
            route="dziewica",
        )
