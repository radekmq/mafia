import random

from characters.character import Ability, Character, RoleType
from logger import log_info
from player import PlayerStatus
from utils_render import render_inactive_page, render_player_page


def ability_effect_introduction(ct_game):
    current_player = ct_game.game_state.get_current_player()
    if not current_player:
        log_info("No current player found for Empata's ability introduction effect.")
        return render_inactive_page(ct_game)
    
    player_character = current_player.character
    if current_player.drunk:
        player_character = current_player.additional_characters[0]

    return render_player_page(ct_game, "player_page_night.html", {
        "role_name": player_character.name,
        "player_link": player_character.route,
        "player_image": player_character.image_path,
        "player_info": player_character.ability.description,
    })

def ability_effect_night_minion(ct_game):
    """Effect of the Empata's ability."""
    return render_inactive_page(ct_game)


def effect_night_all_players(ct_game):
    """Effect of the Empata's ability during night_all_players_action state."""
    log_info("# # # # Setting up Empata's ability. # # # #")
    current_player = ct_game.game_state.get_current_player()
    log_info(f"Empata's ability: {current_player.player_status}.")

    players_in_seat_order = ct_game.game_state.players

    evil_roles = {RoleType.MINION, RoleType.DEMON}
    evil_neighbors_count = 0

    if current_player in players_in_seat_order:
        current_index = players_in_seat_order.index(current_player)
        players_count = len(players_in_seat_order)

        def find_alive_neighbor(step):
            for offset in range(1, players_count):
                candidate = players_in_seat_order[(current_index + step * offset) % players_count]
                if candidate.alive == PlayerStatus.ALIVE:
                    return candidate
            return None

        left_neighbor = find_alive_neighbor(-1)
        right_neighbor = find_alive_neighbor(1)

        for neighbor in [left_neighbor, right_neighbor]:
            if (
                neighbor
                and neighbor.character
                and neighbor.character.role_type in evil_roles
            ):
                evil_neighbors_count += 1

    if current_player.drunk or current_player.poisoned:
        log_info("Empata is drunk or poisoned, false information will be provided.")
        evil_count_faked = random.randint(0, 2)
        
        if evil_count_faked == evil_neighbors_count:
            log_info("Random evil neighbors match actual evil neighbors, we try to randomize again.")
            evil_count_faked = random.randint(0, 2)
        evil_neighbors_count = evil_count_faked
    
    player_status = (
        "Empata wie, że wśród jego sąsiadów jest "
        f"{evil_neighbors_count} złych postaci (Minion lub Demon)"
    )
    current_player.player_status = player_status

    player_character = current_player.character
    if current_player.drunk:
        player_character = current_player.additional_characters[0]

    return render_player_page(
        ct_game,
        "characters/empata/page_night.html",
        {
            "role_name": player_character.name,
            "player_link": player_character.route,
            "player_image": player_character.image_path,
            "player_info": player_character.ability.description,
            "player_status": player_status,
        },
    )


def ability_callback(ct_game, data: dict):
    """Handle callback for the Empata's ability."""


def ability_setup(ct_game, player):
    """Configure for the Empata's ability."""


def on_night_exit(ct_game, player):
    """Handle actions to perform when the night phase ends for the Empata."""


char_ability = Ability(
    description=(
        "Po każdej nocy Empata dowiaduje się, ilu z jego dwóch "
        "żyjących sąsiadów jest złych. Empata uczy się, "
        "czy sąsiadujący z nim gracze są dobrzy czy źli."
    ),
    effect_introduction=ability_effect_introduction,
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
