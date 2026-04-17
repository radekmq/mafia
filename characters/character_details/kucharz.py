import random
from characters.character import Ability, Character, RoleType
from logger import log_info
from utils_render import render_inactive_page, render_player_page


def ability_effect_introduction(ct_game):
    current_player = ct_game.game_state.get_current_player()
    if not current_player:
        log_info("No current player found for Imp's ability introduction effect.")
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
    """Effect of the Kucharz's ability."""
    return render_inactive_page(ct_game)


def effect_night_all_players(ct_game):
    """Effect of the Kucharz's ability during night_all_players_action state."""
    current_player = ct_game.game_state.get_current_player()
    log_info(f"Kucharz's ability: {current_player.player_status}.")

    player_character = current_player.character
    if current_player.drunk:
        player_character = current_player.additional_characters[0]

    return render_player_page(
        ct_game,
        "characters/kucharz/page_night.html",
        {
            "role_name": player_character.name,
            "player_link": player_character.route,
            "player_image": player_character.image_path,
            "player_info": player_character.ability.description,
            "player_status": current_player.player_status,
        },
    )


def ability_callback(ct_game, data: dict):
    """Handle callback for the Kucharz's ability."""


def ability_setup(ct_game, player):
    """Configure for the Kucharz's ability."""
    log_info("# # # # Setting up Kucharz's ability. # # # #")
    if player is None:
        return

    players_in_seat_order = sorted(
        [candidate for candidate in ct_game.game_state.players if candidate.character],
        key=lambda candidate: candidate.seat_no,
    )

    if len(players_in_seat_order) < 2:
        evil_pairs = 0
    else:
        evil_roles = {RoleType.MINION, RoleType.DEMON}
        evil_pairs = 0
        players_count = len(players_in_seat_order)

        for index, current_player in enumerate(players_in_seat_order):
            next_player = players_in_seat_order[(index + 1) % players_count]
            if (
                current_player.character.role_type in evil_roles
                and next_player.character.role_type in evil_roles
            ):
                evil_pairs += 1
            
    if player.drunk:
        log_info("Kucharz is drunk, false information will be provided.")
        from characters.characters_data import CHARACTERS_BY_TYPE
        max_evil_pairs = len(CHARACTERS_BY_TYPE["minion"]) - 1
        log_info(f"Maximum possible evil pairs based on minion characters: {max_evil_pairs}.")
        evil_pairs_faked = random.randint(0, max_evil_pairs)
        if evil_pairs_faked == evil_pairs:
            log_info("Random evil pairs match actual evil pairs, we try to randomize again.")
            evil_pairs_faked = random.randint(0, evil_pairs_faked - 1)
        evil_pairs = evil_pairs_faked

    player.player_status = f"Kucharz wie, że liczba par złych graczy siedzących obok siebie to: {evil_pairs}"


def on_night_exit(ct_game, player):
    """Handle actions to perform when the night phase ends for the Kucharz."""


char_ability = Ability(
    description=(
        "Na początku wiesz, ile par złych graczy siedzi obok siebie. "
        "Kucharz wie, czy źli gracze siedzą obok siebie."
    ),
    effect_introduction=ability_effect_introduction,
    effect_night_minion=ability_effect_night_minion,
    effect_night_all_players=effect_night_all_players,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)


class KucharzCharacter(Character):
    """Class representing the Kucharz character."""

    def __init__(self):
        """Initialize the Kucharz character."""

        super().__init__(
            name="Kucharz",
            role_type=RoleType.TOWNSFOLK,
            ability=char_ability,
            image_path="kucharz.png",
            route="kucharz",
        )
