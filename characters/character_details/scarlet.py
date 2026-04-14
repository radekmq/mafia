from characters.character import Ability, Character, RoleType


def ability_effect_night_minion(ct_game):
    """Effect of the Skarlet's ability."""


def ability_callback(ct_game, data: dict):
    """Handle callback for the Skarlet's ability."""


def ability_setup(ct_game):
    """Configure for the Skarlet's ability."""


def on_night_exit(ct_game):
    """Handle actions to perform when the night phase ends for the Skarlet."""


char_ability = Ability(
    description=(
        "Jeśli przy życiu pozostaje 5 lub więcej graczy, a Demon umrze, stajesz się Demonem. "
        "Skarlet staje się Demonem, gdy Demon umrze."
    ),
    effect_night_minion=ability_effect_night_minion,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)


class SkarletCharacter(Character):
    """Class representing the Skarlet character."""

    def __init__(self):
        """Initialize the Skarlet character."""

        super().__init__(
            name="Skarlet",
            role_type=RoleType.MINION,
            ability=char_ability,
            image_path="skarlet.png",
            route="skarlet",
        )
