
from characters.character import Ability, Character, RoleType
from utils_render import render_inactive_page


def ability_effect_night_minion(ct_game):
    """Effect of the Empata's ability."""
    return render_inactive_page(ct_game)


def effect_night_all_players(ct_game):
    """Effect of the Empata's ability during night_all_players_action state."""
    return render_inactive_page(ct_game)


def ability_callback(ct_game, data: dict):
    """Handle callback for the Empata's ability."""


def ability_setup(ct_game):
    """Configure for the Empata's ability."""


def on_night_exit(ct_game):
    """Handle actions to perform when the night phase ends for the Empata."""


char_ability = Ability(
    description=(
        "Po każdej nocy Empata dowiaduje się, ilu z jego dwóch "
        "żyjących sąsiadów jest złych. Empata uczy się, "
        "czy sąsiadujący z nim gracze są dobrzy czy źli."
    ),
    effect_night_minion=ability_effect_night_minion,
    effect_night_all_players=effect_night_all_players,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)


class EmpataCharacter(Character):
    """Class representing the Empata character."""

    def __init__(self):
        """Initialize the Empata character."""

        super().__init__(
            name="Empata",
            role_type=RoleType.TOWNSFOLK,
            ability=char_ability,
            image_path="empata.png",
            route="empata",
        )
