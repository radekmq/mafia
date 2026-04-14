from characters.character import Ability, Character, RoleType


def ability_effect_night_minion(ct_game):
    """Effect of the Burmistrz's ability."""


def ability_callback(ct_game, data: dict):
    """Handle callback for the Burmistrz's ability."""


def ability_setup(ct_game):
    """Configure for the Burmistrz's ability."""


def on_night_exit(ct_game):
    """Handle actions to perform when the night phase ends for the Burmistrz."""


char_ability = Ability(
    description=(
        "Jeśli przy życiu pozostaje tylko 3 graczy i nie dochodzi do egzekucji, "
        "twoja drużyna wygrywa. Jeśli umrzesz w nocy, zamiast ciebie może zginąć inny gracz. "
        "Burmistrz może wygrać w pokojowy sposób ostatniego dnia."
    ),
    effect_night_minion=ability_effect_night_minion,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)


class BurmistrzCharacter(Character):
    """Class representing the Burmistrz character."""

    def __init__(self):
        """Initialize the Burmistrz character."""
        super().__init__(
            name="Burmistrz",
            role_type=RoleType.TOWNSFOLK,
            ability=char_ability,
            image_path="burmistrz.png",
            route="burmistrz",
        )
