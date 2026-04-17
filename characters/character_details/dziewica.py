from characters.character import Ability, Character, RoleType


def ability_effect_night_minion(ct_game):
    """Effect of the Dziewica's ability."""


def ability_callback(ct_game, data: dict):
    """Handle callback for the Dziewica's ability."""


def ability_setup(ct_game, player):
    """Configure for the Dziewica's ability."""


def on_night_exit(ct_game, player):
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
