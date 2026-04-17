import random

from characters.character import Ability, Character, RoleType
from logger import log_info
from utils_render import render_inactive_page, render_player_page


def ability_effect_introduction(ct_game):
    current_player = ct_game.game_state.get_current_player()
    if not current_player:
        log_info("No current player found for Bibliotekarka's ability introduction effect.")
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
    """Effect of the Bibliotekarka's ability."""
    return render_inactive_page(ct_game)


def effect_night_all_players(ct_game):
    """Effect of the Bibliotekarka's ability during night_all_players_action state."""
    current_player = ct_game.game_state.get_current_player()
    log_info(f"Bibliotekarka's ability: {current_player.player_status}.")

    player_character = current_player.character
    if current_player.drunk:
        player_character = current_player.additional_characters[0]

    return render_player_page(
        ct_game,
        "characters/bibliotekarka/page_night.html",
        {
            "role_name": player_character.name,
            "player_link": player_character.route,
            "player_image": player_character.image_path,
            "player_info": player_character.ability.description,
            "player_status": current_player.player_status,
        },
    )


def ability_callback(ct_game, data: dict):
    """Handle callback for the Bibliotekarka's ability."""


def ability_setup(ct_game, player):
    """Configure for the Bibliotekarka's ability."""
    log_info("# # # # Setting up Bibliotekarka's ability. # # # #")

    if player is None:
        return

    outsiders_in_play = [
        candidate
        for candidate in ct_game.game_state.players
        if (
            candidate.character
            and candidate.character.role_type == RoleType.OUTSIDER
            and candidate.client_id != player.client_id
        )
    ]
    
    if player.drunk:
        log_info("Bibliotekarka is drunk, false information will be provided.")

        from characters.characters_data import CHARACTERS_BY_TYPE
        if not CHARACTERS_BY_TYPE["outsider"]:
            player.player_status = (
                "W puli brak Outsiderów do wskazania."
            )
            return

        outsider_character = random.choice(CHARACTERS_BY_TYPE["outsider"])
        log_info(f"Bibliotekarka's ability setup: chosen random outsider character is {outsider_character.name}.")
        eligible_players = [
            candidate
            for candidate in ct_game.game_state.players
            if candidate.client_id != player.client_id
        ]

        shown_players = random.sample(eligible_players, min(2, len(eligible_players)))
        log_info(f"Bibliotekarka's ability setup: initially chosen players to show are {[p.name for p in shown_players]}.")
        matching_index = next(
            (
                i
                for i, c in enumerate(shown_players)
                if c.character and c.character.name == outsider_character.name
            ),
            None,
        )

        if matching_index is not None:
            log_info(f"Bibliotekarka's ability setup: found matching player {shown_players[matching_index].name} for the chosen outsider character.")
            other_player = shown_players[1 - matching_index]

            # losujemy ponownie, ale wykluczamy tylko tego drugiego gracza
            pool = [p for p in eligible_players if p.client_id != other_player.client_id]

            shown_players[matching_index] = random.choice(pool)
            log_info(f"Bibliotekarka's ability setup: replaced matching player with {shown_players[matching_index].name} from the pool.")
            
        shown_players_text = " lub ".join(
            f"{candidate.name} (miejsce: {candidate.seat_no})"
            for candidate in shown_players
        )
        
        if len(shown_players) < 2:
            shown_players_text = "brak graczy do wskazania"
            
        player.player_status = (
            f"Bibliotekarka wie, że jednen z graczy: {shown_players_text} "
            f"ma postać: {outsider_character.name}."
        )
        log_info(f"Bibliotekarka's status: {player.player_status}")
        return

    if outsiders_in_play:
        outsider_player = random.choice(outsiders_in_play)
        decoy_candidates = [
            candidate
            for candidate in ct_game.game_state.players
            if (
                candidate.client_id != outsider_player.client_id
                and candidate.client_id != player.client_id
            )
        ]
        shown_players = [outsider_player]
        if decoy_candidates:
            shown_players.append(random.choice(decoy_candidates))
        random.shuffle(shown_players)

        shown_players_text = " lub ".join(
            f"{candidate.name} (miejsce: {candidate.seat_no})"
            for candidate in shown_players
        )
        player.player_status = (
            f"Bibliotekarka wie, że jeden z graczy: {shown_players_text} "
            f"ma postać: {outsider_player.character.name}."
        )
        return

    player.player_status = (
        "Bibliotekarka nie otrzymuje informacji, bo w puli brak Outsiderów."
    )


def on_night_exit(ct_game, player):
    """Handle actions to perform when the night phase ends for the Bibliotekarka."""


char_ability = Ability(
    description=(
        "Na początku wiesz, że 1 z 2 graczy jest konkretnym Outsiderem "
        "(lub że żaden nie jest w grze). Bibliotekarka dowiaduje się, "
        "że konkretny Outsider jest w grze, ale nie kto go gra."
    ),
    effect_introduction=ability_effect_introduction,
    effect_night_minion=ability_effect_night_minion,
    effect_night_all_players=effect_night_all_players,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)


class BibliotekarkaCharacter(Character):
    """Class representing the Bibliotekarka character."""

    def __init__(self):
        """Initialize the Bibliotekarka character."""

        super().__init__(
            name="Bibliotekarka",
            role_type=RoleType.TOWNSFOLK,
            ability=char_ability,
            image_path="bibliotekarka.png",
            route="bibliotekarka",
        )
