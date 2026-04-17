import random

from characters.character import Ability, Character, RoleType
from logger import log_info
from utils_render import render_inactive_page, render_player_page


def ability_effect_introduction(ct_game):
    current_player = ct_game.game_state.get_current_player()
    if not current_player:
        log_info("No current player found for Dead's ability introduction effect.")
        return render_inactive_page(ct_game)
    
    player_character = current_player.character

    return render_player_page(ct_game, "player_page_night.html", {
        "role_name": player_character.name,
        "player_link": player_character.route,
        "player_image": player_character.image_path,
        "player_info": player_character.ability.description,
    })

def ability_effect_night_minion(ct_game):
    """Effect of the Wyeliminowany's ability during night_minion_action state."""
    return render_inactive_page(ct_game)

def effect_night_all_players(ct_game):
    """Effect of the Wyeliminowany's ability during night_all_players_action state."""
    current_player = ct_game.game_state.get_current_player()
    log_info(f"Dead's effect for night.")

    player_character = current_player.character

    return render_player_page(
        ct_game,
        "player_page_night.html",
        {
            "role_name": player_character.name,
            "player_link": player_character.route,
            "player_image": player_character.image_path,
            "player_info": player_character.ability.description,
        },
    )
    
def ability_callback(ct_game, data: dict):
    """Handle callback for the Wyeliminowany's ability."""
    
def ability_setup(ct_game, player):
    """Configure for the Wyeliminowany's ability."""

def on_night_exit(ct_game, player):
    """Handle actions when exiting night phase for the Wyeliminowany character."""
    

char_ability = Ability(
    description=(
        "Jesteć wyeliminowany z gry, nie posiadasz żadnej zdolności aktywnej."
    ),
    effect_introduction=ability_effect_introduction,
    effect_night_minion=ability_effect_night_minion,
    effect_night_all_players=effect_night_all_players,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)

class DeadCharacter(Character):
    """Class representing the Wyeliminowany character."""

    def __init__(self):
        """Initialize the Wyeliminowany character."""

        super().__init__(
            name="Wyeliminowany",
            role_type=RoleType.DEAD,
            ability=char_ability,
            image_path="dead.png",
            route="dead",
        )
