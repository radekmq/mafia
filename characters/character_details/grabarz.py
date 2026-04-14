from characters.character import Ability, Character, RoleType


def ability_effect_night_minion(ct_game):
    """Effect of the Grabarz's ability."""


def ability_callback(ct_game, data: dict):
    """Handle callback for the Grabarz's ability."""


def ability_setup(ct_game):
    """Configure for the Grabarz's ability."""


def on_night_exit(ct_game):
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
