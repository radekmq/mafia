from characters.character import Ability, Character, RoleType
from game_state import GameState


def ability_effect_night_minion(game_state: GameState):
    """Effect of the Żołnierz's ability."""


def ability_callback(game_state: GameState, data: dict):
    """Handle callback for the Żołnierz's ability."""


def ability_setup(game_state: GameState):
    """Configure for the Żołnierz's ability."""


def on_night_exit(game_state: GameState):
    """Handle actions to perform when the night phase ends for the Żołnierz."""


char_ability = Ability(
    description=(
        "Jesteś bezpieczny przed Demonem. "
        "Żołnierz (Soldier) nie może zostać zabity przez Demona."
    ),
    effect_night_minion=ability_effect_night_minion,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)


class ZolnierzCharacter(Character):
    """Class representing the Żołnierz character."""

    def __init__(self):
        """Initialize the Żołnierz character."""

        super().__init__(
            name="Zolnierz",
            role_type=RoleType.TOWNSFOLK,
            ability=char_ability,
            image_path="zolnierz.png",
            route="zolnierz",
        )
