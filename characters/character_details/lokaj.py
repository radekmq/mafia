from characters.character import Ability, Character, RoleType


def ability_effect_night_minion(ct_game):
    """Effect of the Lokaj's ability."""


def ability_callback(ct_game, data: dict):
    """Handle callback for the Lokaj's ability."""


def ability_setup(ct_game, player):
    """Configure for the Lokaj's ability."""


def on_night_exit(ct_game, player):
    """Handle actions to perform when the night phase ends for the Lokaj."""


char_ability = Ability(
    description=(
        "Każdej nocy wybierz gracza (nie siebie): jutro możesz głosować tylko wtedy, "
        "gdy on również głosuje."
        "Lokaj może głosować tylko wtedy, gdy jego Pan (inny gracz) również głosuje."
    ),
    effect_night_minion=ability_effect_night_minion,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)


class LokajCharacter(Character):
    """Class representing the Lokaj character."""

    def __init__(self):
        """Initialize the Lokaj character."""

        super().__init__(
            name="Lokaj",
            role_type=RoleType.OUTSIDER,
            ability=char_ability,
            image_path="lokaj.png",
            route="lokaj",
        )
