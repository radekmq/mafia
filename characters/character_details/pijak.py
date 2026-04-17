import json

from characters.character import Ability, Character, RoleType
from logger import log_info
from player import PlayerStatus
from utils_render import render_inactive_page, render_player_page


def ability_effect_introduction(ct_game):
    current_player = ct_game.game_state.get_current_player()
    if not current_player:
        log_info("No current player found for Pijak's ability introduction effect.")
        return render_inactive_page(ct_game)
    
    if not current_player.additional_characters:
        log_info("No additional characters found for Pijak's ability introduction effect.")
        return render_inactive_page(ct_game)
    
    drunk_character = current_player.additional_characters[0]

    return render_player_page(ct_game, "player_page_night.html", {
        "role_name": drunk_character.name,
        "player_link": drunk_character.route,
        "player_image": drunk_character.image_path,
        "player_info": drunk_character.ability.description,
    })

def effect_night_all_players(ct_game):
    """Effect of the Pijak's ability."""
    log_info("Pijak's ability effect_night_all_players called, forwarding to additional character's ability effect.")
    current_player = ct_game.game_state.get_current_player()
    return current_player.additional_characters[0].ability.effect_night_all_players(ct_game)
    
def ability_effect_night_minion(ct_game):
    """Effect of the Pijak's ability."""
    log_info("Pijak's ability effect_night_minion called, forwarding to additional character's ability effect.")
    current_player = ct_game.game_state.get_current_player()
    return current_player.additional_characters[0].ability.effect_night_minion(ct_game)


def ability_callback(ct_game, data: dict):
    """Handle callback for the Pijak's ability."""
    log_info("Pijak's ability callback called, forwarding to additional character's ability callback.")
    current_player = ct_game.game_state.get_current_player()
    return current_player.additional_characters[0].ability.callback_night(ct_game, data)


def ability_setup(ct_game, player):
    """Configure for the Pijak's ability."""
    log_info("Setting up Pijak's ability forwarding to additional character's ability.")
    return player.additional_characters[0].ability.setup(ct_game, player)


def on_night_exit(ct_game, player):
    """Handle actions to perform when the night phase ends for the Pijak."""
    return player.additional_characters[0].ability.on_night_exit(ct_game, player)


char_ability = Ability(
    description=(
        "Nie wiesz, że jesteś Pijakiem. Myślisz, że jesteś "
        "postacią z grupy Townsfolk, ale nią nie jesteś."
    ),
    effect_introduction=ability_effect_introduction,
    effect_night_minion=ability_effect_night_minion,
    effect_night_all_players=effect_night_all_players,
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
