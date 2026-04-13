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
    ct_game.game_state.nominated_by_imp_to_die = None

    if current_player is None:
        log_info("No current player found for Imp's ability effect.")
        return "No current player found."

    if ct_game.state != "night_all_players_action":
        log_info(
            "Imp's ability effect called outside of night_all_players_action state."
        )
        return render_inactive_page(ct_game)

    if current_player.character.first_night_action_done is False:
        current_player.character.first_night_action_done = True
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

    player_list = []
    for player in ct_game.game_state.players:
        if player.alive == PlayerStatus.ALIVE:
            player_list.append(
                (f"{player.name} (miejsce: {player.seat_no})", player.client_id)
            )
    log_info(f"Player list for Imp's ability effect: {player_list}")

    list_of_extra_chars = [
        player.name for player in current_player.additional_characters
    ]
    list_of_minions = [
        player.name
        for player in ct_game.game_state.players
        if player.character.role_type == RoleType.MINION
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


def ability_callback(ct_game, data: dict):
    """Handle callback for the Imp's ability."""
    log_info(f"Imp's ability callback called with data: {data}")

    ct_game.game_state.nominated_by_imp_to_die = data.get("selected")
    log_info(
        f"Player nominated by Imp to die: {ct_game.game_state.nominated_by_imp_to_die}"
    )

    current_player = ct_game.game_state.get_current_player()
    player_to_die = ct_game.game_state.get_player_by_client_id(
        ct_game.game_state.nominated_by_imp_to_die[0]
    )
    log_info(
        f"Player selected to die by Imp: {player_to_die.name if player_to_die else 'None'}"
    )

    if current_player is not None:
        current_player.character.imp_night_status = (
            "\nImp selected player to die: " + str(player_to_die.name)
        )
    ct_game.game_state.get_current_player().night_action_done = True
    return "Selected player: " + player_to_die.name


def ability_setup(ct_game):
    """Configure for the Imp's ability."""
    # There is no Configure for the Imp's ability
    current_player = ct_game.game_state.get_current_player()
    current_player.character.first_night_action_done = False


def on_night_exit(ct_game):
    """Handle actions to perform when the night phase ends for the Imp."""
    # There are no specific actions to perform when the night phase ends for the Imp
    current_player = ct_game.game_state.get_current_player()
    if current_player is not None:
        current_player.night_action_done = False


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
