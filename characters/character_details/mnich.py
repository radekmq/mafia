from characters.character import Ability, Character, RoleType


def ability_effect_night_minion(ct_game):
    """Effect of the Mnich's ability."""


def ability_callback(ct_game, data: dict):
    """Handle callback for the Mnich's ability."""


def ability_setup(ct_game, player):
    """Configure for the Mnich's ability."""


def on_night_exit(ct_game, player):
    """Handle actions to perform when the night phase ends for the Mnich."""


char_ability = Ability(
    description=(
        "Każdej nocy wybierz gracza (nie siebie): tej nocy jest on bezpieczny przed Demonem."
        "Mnich chroni innych graczy przed Demonem."
    ),
    effect_night_minion=ability_effect_night_minion,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)


class MnichCharacter(Character):
    """Class representing the Mnich character."""

    def __init__(self):
        """Initialize the Mnich character."""

        super().__init__(
            name="Mnich",
            role_type=RoleType.TOWNSFOLK,
            ability=char_ability,
            image_path="mnich.png",
            route="mnich",
        )
