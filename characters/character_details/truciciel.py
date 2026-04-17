import json

from characters.character import Ability, Character, RoleType
from logger import log_info
from player import PlayerStatus
from utils_render import render_inactive_page, render_player_page


def ability_effect_introduction(ct_game):
    current_player = ct_game.game_state.get_current_player()
    if not current_player:
        log_info("No current player found for Truciciel's ability introduction effect.")
        return render_inactive_page(ct_game)

    return render_player_page(ct_game, "player_page_night.html", {
        "role_name": current_player.character.name,
        "player_link": current_player.character.route,
        "player_image": current_player.character.image_path,
        "player_info": current_player.character.ability.description,
    })


def ability_effect_night_minion(ct_game):
    """Effect of the Truciciel's ability."""
    log_info("Truciciel's ability effect for night_minion_action called.")
    current_player = ct_game.game_state.get_current_player()

    if current_player is None:
        log_info("No current player found for Truciciel's ability effect.")
        return "No current player found."

    if (
        ct_game.state != "night_all_players_action"
        and ct_game.state != "night_minion_action"
    ):
        log_info("Truciciel's ability effect called outside of night_action state.")
        return render_inactive_page(ct_game)

    player_list = []
    for player in ct_game.game_state.players:
        if (
            player.alive == PlayerStatus.ALIVE
            and player.client_id != current_player.client_id
        ):
            is_minion = (
                ", Minion" if player.character.role_type == RoleType.MINION else ""
            )
            is_demon = ", Demon" if player.character.role_type == RoleType.DEMON else ""
            player_list.append(
                (
                    f"{player.name} (miejsce: {player.seat_no}{is_minion}{is_demon})",
                    player.client_id,
                )
            )
    log_info(f"Player list for Truciciel's ability effect: {player_list}")

    list_of_minions = [
        player.name
        for player in ct_game.game_state.players
        if player.character and player.character.role_type == RoleType.MINION
    ]
    if not list_of_minions:
        list_of_minions = ["Brak Minionów w grze"]

    demon = [
        player.name
        for player in ct_game.game_state.players
        if player.character and player.character.role_type == RoleType.DEMON
    ]

    return render_player_page(
        ct_game,
        "characters/truciciel/page_night.html",
        {
            "role_name": current_player.character.name,
            "player_link": current_player.character.route,
            "player_image": current_player.character.image_path,
            "player_info": current_player.character.ability.description,
            "allow_truciciel_night_action": not current_player.night_action_done,
            "player_list": player_list,
            "truciciel_status": current_player.character.truciciel_night_status,
            "demon": demon[0] if demon else None,
            "minions": ", ".join(list_of_minions),
        },
    )


def ability_callback(ct_game, data):
    """Handle callback for the Truciciel's ability."""
    log_info(f"Truciciel's ability callback called with data: {data}")

    try:
        selected_json = json.loads(data.get("selected_json", "[]"))
    except json.JSONDecodeError:
        selected_json = []

    log_info(f"Player nominated by Truciciel to poison: {selected_json}")

    current_player = ct_game.game_state.get_current_player()
    current_player.night_action_done = True
    poisoned_character = ct_game.game_state.get_player_by_client_id(selected_json[0])
    poisoned_character.poisoned = True
    log_info(
        f"Gracz otruty: {poisoned_character.name if poisoned_character else 'None'}"
    )
    current_player.character.truciciel_night_status = (
        f"\nGracz {poisoned_character.name} został otruty."
    )
    current_player.confirm_minion_action()
    return ability_effect_night_minion(ct_game)


def ability_setup(ct_game, player):
    """Configure for the Truciciel's ability."""


def on_night_exit(ct_game, player):
    """Handle actions to perform when the night phase ends for the Truciciel."""
    log_info("Truciciel's on_night_exit called.")

    player = ct_game.game_state.get_player_by_character_name("Truciciel")
    if player is None:
        return

    player.night_action_done = False
    player.character.truciciel_night_status = None


char_ability = Ability(
    description=(
        "Każdej nocy wybierz gracza: tej nocy i następnego dnia "
        "ten gracz jest zatruty. Truciciel potajemnie zakłóca "
        "działanie zdolności postaci."
    ),
    effect_introduction=ability_effect_introduction,
    effect_night_minion=ability_effect_night_minion,
    effect_night_all_players=ability_effect_night_minion,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)


class TrucicielCharacter(Character):
    """Class representing the Truciciel character."""

    def __init__(self):
        """Initialize the Truciciel character."""

        super().__init__(
            name="Truciciel",
            role_type=RoleType.MINION,
            ability=char_ability,
            image_path="truciciel.png",
            route="truciciel",
        )

        self.truciciel_night_status = None
