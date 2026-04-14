import random

from characters.character import Ability, Character, RoleType
from logger import log_info
from utils_render import render_inactive_page, render_player_page


def ability_effect_night_minion(ct_game):
    """Effect of the Detektyw's ability."""
    return render_inactive_page(ct_game)


def effect_night_all_players(ct_game):
    """Effect of the Detektyw's ability during night_all_players_action state."""
    current_player = ct_game.game_state.get_current_player()
    log_info(f"Detektyw's ability: {current_player.player_status}.")

    return render_player_page(
        ct_game,
        "characters/detektyw/page_night.html",
        {
            "player_status": current_player.player_status,
        },
    )


def ability_callback(ct_game, data: dict):
    """Handle callback for the Detektyw's ability."""


def ability_setup(ct_game):
    """Configure for the Detektyw's ability."""
    log_info("Setting up Detektyw's ability.")
    player = ct_game.game_state.get_player_by_character_name("Detektyw")
    if player is None:
        return

    minions_in_play = [
        candidate
        for candidate in ct_game.game_state.players
        if candidate.character and candidate.character.role_type == RoleType.MINION
    ]

    if minions_in_play:
        minion_player = random.choice(minions_in_play)
        decoy_candidates = [
            candidate
            for candidate in ct_game.game_state.players
            if candidate.client_id != minion_player.client_id
        ]
        shown_players = [minion_player]
        if decoy_candidates:
            shown_players.append(random.choice(decoy_candidates))
        random.shuffle(shown_players)

        shown_players_text = " lub ".join(
            f"{candidate.name} (miejsce: {candidate.seat_no})"
            for candidate in shown_players
        )
        player.player_status = (
            f"Detektyw wie, że jednym z graczy: {shown_players_text} "
            f"jest {minion_player.character.name}."
        )
        return

    player.player_status = "Detektyw nie otrzymuje informacji, bo w puli brak Minionów."


def on_night_exit(ct_game):
    """Handle actions to perform when the night phase ends for the Detektyw."""


char_ability = Ability(
    description=(
        "Na początku wiesz, że 1 z 2 graczy jest konkretnym Minionem. "
        "Detektyw dowiaduje się, że konkretny Minion jest w grze, "
        "ale nie kto go gra."
    ),
    effect_night_minion=ability_effect_night_minion,
    effect_night_all_players=effect_night_all_players,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)


class DetektywCharacter(Character):
    """Class representing the Detektyw character."""

    def __init__(self):
        """Initialize the Detektyw character."""

        super().__init__(
            name="Detektyw",
            role_type=RoleType.TOWNSFOLK,
            ability=char_ability,
            image_path="detektyw.png",
            route="detektyw",
        )
