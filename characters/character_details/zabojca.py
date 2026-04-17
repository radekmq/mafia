from characters.character import Ability, Character, RoleType


def ability_effect_night_minion(ct_game):
    """Effect of the Zabójca's ability."""


def ability_callback(ct_game, data: dict):
    """Handle callback for the Zabójca's ability."""


def ability_setup(ct_game, player):
    """Configure for the Zabójca's ability."""


def on_night_exit(ct_game, player):
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
