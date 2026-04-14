import random

from characters.character import Ability, Character, RoleType
from logger import log_info
from utils_render import render_inactive_page, render_player_page


def ability_effect_night_minion(ct_game):
    """Effect of the Bibliotekarka's ability."""
    return render_inactive_page(ct_game)


def effect_night_all_players(ct_game):
    """Effect of the Bibliotekarka's ability during night_all_players_action state."""
    current_player = ct_game.game_state.get_current_player()
    log_info(f"Bibliotekarka's ability: {current_player.player_status}.")

    return render_player_page(
        ct_game,
        "characters/bibliotekarka/page_night.html",
        {
            "player_status": current_player.player_status,
        },
    )


def ability_callback(ct_game, data: dict):
    """Handle callback for the Bibliotekarka's ability."""


def ability_setup(ct_game):
    """Configure for the Bibliotekarka's ability."""
    log_info("Setting up Bibliotekarka's ability.")
    player = ct_game.game_state.get_player_by_character_name("Bibliotekarka")
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
            f"Bibliotekarka wie, że jednym z graczy: {shown_players_text} "
            f"jest {outsider_player.character.name}."
        )
        return

    from characters.characters_data import CHARACTERS_BY_TYPE

    available_outsiders = CHARACTERS_BY_TYPE["outsider"]
    if available_outsiders:
        absent_outsider = random.choice(available_outsiders)
        player.player_status = (
            f"Bibliotekarka wie, że {absent_outsider.name} nie ma w tej grze."
        )
        return

    player.player_status = (
        "Bibliotekarka nie otrzymuje informacji, bo w puli brak Outsiderów."
    )


def on_night_exit(ct_game):
    """Handle actions to perform when the night phase ends for the Bibliotekarka."""


char_ability = Ability(
    description=(
        "Na początku wiesz, że 1 z 2 graczy jest konkretnym Outsiderem "
        "(lub że żaden nie jest w grze). Bibliotekarka dowiaduje się, "
        "że konkretny Outsider jest w grze, ale nie kto go gra."
    ),
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
