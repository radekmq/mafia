from characters.character import Ability, Character, RoleType


def ability_effect_night_minion(ct_game):
    """Effect of the Pijak's ability."""


def ability_callback(ct_game, data: dict):
    """Handle callback for the Pijak's ability."""


def ability_setup(ct_game):
    """Configure for the Pijak's ability."""


def on_night_exit(ct_game):
    """Handle actions to perform when the night phase ends for the Pijak."""


char_ability = Ability(
    description=(
        "Nie wiesz, że jesteś Pijakiem. Myślisz, że jesteś "
        "postacią z grupy Townsfolk, ale nią nie jesteś."
    ),
    effect_night_minion=ability_effect_night_minion,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)


class PijakCharacter(Character):
    """Class representing the Pijak character."""

    def __init__(self):
        """Initialize the Pijak character."""

        super().__init__(
            name="Pijak",
            role_type=RoleType.OUTSIDER,
            ability=char_ability,
            image_path="pijak.png",
            route="pijak",
        )
