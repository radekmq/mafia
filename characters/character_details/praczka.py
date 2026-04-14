import random

from characters.character import Ability, Character, RoleType
from logger import log_info
from utils_render import render_inactive_page, render_player_page


def ability_effect_night_minion(ct_game):
    """Effect of the Praczka's ability."""
    return render_inactive_page(ct_game)


def effect_night_all_players(ct_game):
    """Effect of the Praczka's ability during night_all_players_action state."""
    current_player = ct_game.game_state.get_current_player()
    log_info(f"Praczka's ability: {current_player.player_status}.")

    return render_player_page(
        ct_game,
        "characters/praczka/page_night.html",
        {
            "player_status": current_player.player_status,
        },
    )


def ability_callback(ct_game, data: dict):
    """Handle callback for the Praczka's ability."""


def ability_setup(ct_game):
    """Configure for the Praczka's ability."""
    log_info("Setting up Praczka's ability.")
    player = ct_game.game_state.get_player_by_character_name("Praczka")
    if player is None:
        return

    townsfolk_in_play = [
        candidate
        for candidate in ct_game.game_state.players
        if (
            candidate.character
            and candidate.character.role_type == RoleType.TOWNSFOLK
            and candidate.character.name != "Praczka"
            and candidate.client_id != player.client_id
        )
    ]

    if not townsfolk_in_play:
        player.player_status = "Praczka nie otrzymuje informacji o Mieszczaninie."
        return

    townsfolk_player = random.choice(townsfolk_in_play)
    decoy_candidates = [
        candidate
        for candidate in ct_game.game_state.players
        if candidate.client_id != townsfolk_player.client_id
        and candidate.client_id != player.client_id
    ]
    shown_players = [townsfolk_player]
    if decoy_candidates:
        shown_players.append(random.choice(decoy_candidates))
    else:
        player.player_status = "Praczka nie otrzymuje informacji o Mieszczaninie."
        return
    random.shuffle(shown_players)

    shown_players_text = "\n * " + "\n * ".join(
        f"{candidate.name} (miejsce: {candidate.seat_no})"
        for candidate in shown_players
    )
    player.player_status = (
        f"Praczka wie, że jeden z graczy: {shown_players_text} \n"
        f"ma postać: {townsfolk_player.character.name}."
    )


def on_night_exit(ct_game):
    """Handle actions to perform when the night phase ends for the Praczka."""


char_ability = Ability(
    description=(
        "Zaczynasz grę wiedząc, że 1 z 2 graczy jest konkretną postacią Mieszczanina. "
        "Praczka dowiaduje się, że dana postać Mieszczanina jest w grze, "
        "ale nie wie, który gracz ją posiada."
    ),
    effect_night_minion=ability_effect_night_minion,
    effect_night_all_players=effect_night_all_players,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)


class PraczkaCharacter(Character):
    """Class representing the Praczka character."""

    def __init__(self):
        """Initialize the Praczka character."""

        super().__init__(
            name="Praczka",
            role_type=RoleType.TOWNSFOLK,
            ability=char_ability,
            image_path="praczka.png",
            route="praczka",
        )
