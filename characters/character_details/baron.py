from characters.character import Ability, Character, RoleType


def ability_effect_night_minion(ct_game):
    """Effect of the Baron's ability."""


def ability_callback(ct_game, data: dict):
    """Handle callback for the Baron's ability."""


def ability_setup(ct_game):
    """Configure for the Baron's ability."""


def on_night_exit(ct_game):
    """Handle actions to perform when the night phase ends for the Baron."""


char_ability = Ability(
    description=(
        "W grze jest dodatkowa liczba Outsiderów. [+2 Outsiderów] "
        "Baron zmienia liczbę Outsiderów obecnych w grze."
    ),
    effect_night_minion=ability_effect_night_minion,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)


class BaronCharacter(Character):
    """Class representing the Baron character."""

    def __init__(self):
        """Initialize the Baron character."""

        super().__init__(
            name="Baron",
            role_type=RoleType.MINION,
            ability=char_ability,
            image_path="baron.png",
            route="baron",
        )
