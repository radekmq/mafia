import json

from characters.character import Ability, Character, RoleType
from logger import log_info
from player import PlayerStatus
from utils_render import render_inactive_page, render_player_page


def ability_effect_night_minion(ct_game):
    return render_inactive_page(ct_game)


def effect_night_all_players(ct_game):
    """Effect of the Imp's ability."""
    night_action_allowed = True
    current_player = ct_game.game_state.get_current_player()

    if current_player is None:
        log_info("No current player found for Imp's ability effect.")
        return "No current player found."

    if ct_game.state != "night_all_players_action":
        log_info(
            "Imp's ability effect called outside of night_all_players_action state."
        )
        return render_inactive_page(ct_game)

    if current_player.character.first_night_action_done is False:
        log_info("First night action for Imp, skipping night action effect.")
        current_player.character.imp_night_status = (
            "Pierwszej nocy Imp nie wykonuje akcji eliminacji gracza."
        )
        night_action_allowed = False

    elif current_player.night_action_done is True:
        log_info(
            "Night action already done for current player, skipping night action effect."
        )
        night_action_allowed = False

    has_alive_minion = any(
        player.alive == PlayerStatus.ALIVE
        and player.character is not None
        and player.character.role_type == RoleType.MINION
        for player in ct_game.game_state.players
    )

    player_list = []
    for player in ct_game.game_state.players:
        if player.alive == PlayerStatus.ALIVE:
            if (
                not has_alive_minion
                and player.character is not None
                and player.character.name == "Imp"
            ):
                continue
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
    log_info(f"Player list for Imp's ability effect: {player_list}")

    list_of_extra_chars = [
        player.name for player in current_player.additional_characters
    ]
    list_of_minions = [
        player.name
        for player in ct_game.game_state.players
        if player.character is not None
        and player.character.role_type == RoleType.MINION
    ]
    if not list_of_minions:
        list_of_minions = ["Brak Minionów w grze"]

    return render_player_page(
        ct_game,
        "characters/imp/page_night.html",
        {
            "allow_imp_night_action": night_action_allowed,
            "player_list": player_list,
            "imp_status": current_player.character.imp_night_status,
            "imp_extra_chars": ", ".join(list_of_extra_chars),
            "imp_minions": ", ".join(list_of_minions),
        },
    )


def ability_callback(ct_game, data, replace_demon=False):
    """Handle callback for the Imp's ability."""
    log_info(f"Imp's ability callback called with data: {data}")

    try:
        selected_json = json.loads(data.get("selected_json", "[]"))
    except json.JSONDecodeError:
        selected_json = []

    if not selected_json:
        log_info("No player selected in Imp's ability callback.")
        return effect_night_all_players(ct_game)

    current_player = ct_game.game_state.get_current_player()
    player_selected = ct_game.game_state.get_player_by_client_id(selected_json[0])

    if player_selected is None:
        log_info("Selected player for Imp's ability callback not found.")
        return effect_night_all_players(ct_game)

    if replace_demon:
        log_info(f"Player selected for Demon replacement: {player_selected.name}")
        ct_game.game_state.demon_replacement_candidate = player_selected
        return effect_night_all_players(ct_game)

    ct_game.game_state.nominated_by_imp_to_die = player_selected

    log_info(f"Player nominated by Imp to die: {player_selected.name}")

    current_player.character.imp_night_status = (
        "\nImp planuje wyeliminować gracza: " + str(player_selected.name)
    )
    ct_game.game_state.get_current_player().night_action_done = True

    if current_player.poisoned:
        log_info("Current player is poisoned, skipping Imp's night action effect.")
        ct_game.game_state.nominated_by_imp_to_die = None

    if player_selected.client_id == current_player.client_id:
        log_info(
            "Imp has nominated themselves to die, setting up for Demon replacement."
        )
        current_player.character.imp_night_status = (
            "\nWybrałeś siebie, więc jeden z Minionów prawdopodobnie zostanie Impem!"
        )
        alive_minions = [
            player
            for player in ct_game.game_state.players
            if player.alive == PlayerStatus.ALIVE
            and player.character is not None
            and player.character.role_type == RoleType.MINION
        ]

        if len(alive_minions) == 1:
            ct_game.game_state.demon_replacement_candidate = alive_minions[0]
            log_info(
                "Only one alive Minion found. Auto-setting Demon replacement candidate: "
                f"{alive_minions[0].name}"
            )
            return effect_night_all_players(ct_game)

        player_list = []
        for player in ct_game.game_state.players:
            if (
                player.alive == PlayerStatus.ALIVE
                and player.character is not None
                and player.character.role_type == RoleType.MINION
            ):
                is_minion = ", Minion"
                player_list.append(
                    (
                        f"{player.name} - {is_minion} (miejsce: {player.seat_no})",
                        player.client_id,
                    )
                )
        log_info(f"Player list for Imp's ability effect: {player_list}")

        return render_player_page(
            ct_game,
            "characters/imp/page_replace_demon.html",
            {
                "player_list": player_list,
            },
        )

    return effect_night_all_players(ct_game)


def ability_setup(ct_game):
    """Configure for the Imp's ability."""
    # There is no Configure for the Imp's ability
    player = ct_game.game_state.get_player_by_character_name("Imp")
    if player is None:
        return

    player.character.first_night_action_done = False


def on_night_exit(ct_game):
    """Handle actions to perform when the night phase ends for the Imp."""
    # There are no specific actions to perform when the night phase ends for the Imp
    log_info("Imp's on_night_exit called.")

    player = ct_game.game_state.get_player_by_character_name("Imp")
    if player is None:
        return

    player.night_action_done = False
    player.character.first_night_action_done = True


imp_ability = Ability(
    description=(
        "Każdej nocy, wybierz gracza: ten gracz umiera. "
        "Jeśli w ten sposób zabijesz samego siebie, jeden z Minionów "
        "staje się Impem. Imp zabija jednego gracza każdej nocy."
    ),
    effect_night_minion=ability_effect_night_minion,
    effect_night_all_players=effect_night_all_players,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)


class ImpCharacter(Character):
    """Class representing the Imp character."""

    def __init__(self):
        """Initialize the Imp character."""

        super().__init__(
            name="Imp",
            role_type=RoleType.DEMON,
            ability=imp_ability,
            image_path="imp.png",
            route="imp",
        )

        self.imp_night_status = None
        self.first_night_action_done = False
