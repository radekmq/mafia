
from characters.character import Ability, Character, RoleType


def ability_effect_night_minion(ct_game):
    """Effect of the Krukarz's ability."""


def ability_callback(ct_game, data: dict):
    """Handle callback for the Krukarz's ability."""


def ability_setup(ct_game):
    """Configure for the Krukarz's ability."""


def on_night_exit(ct_game):
    """Handle actions to perform when the night phase ends for the Krukarz."""


char_ability = Ability(
    description=(
        "Jeśli umrzesz w nocy, zostajesz obudzony, aby wybrać gracza: poznajesz jego postać. "
        "Jeśli Krukarz umrze w nocy, może poznać postać jednego gracza."
    ),
    effect_night_minion=ability_effect_night_minion,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)


class KrukarzCharacter(Character):
    """Class representing the Krukarz character."""

    def __init__(self):
        """Initialize the Krukarz character."""

        super().__init__(
            name="Krukarz",
            role_type=RoleType.TOWNSFOLK,
            ability=char_ability,
            image_path="krukarz.png",
            route="krukarz",
        )
