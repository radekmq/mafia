# from characters.character_details.dead import DeadCharacter
import random

from characters.character import Ability, Character, DualEffect, RenderPage, RoleType
from game_events import Event
from logger import log_info
from player import PlayerStatus

# = = = = = = = = = = = = =  RENDER PAGE = = = = = = = = = = = = =


def render_introduction(game_engine, current_player):
    """Render effect of the Imps's ability during the introduction phase."""
    player_character = current_player.character
    return {
        "screen": "players_introduction",
        "character_data": {
            "role_name": player_character.name,
            "player_link": player_character.route,
            "player_image": player_character.image_path,
            "player_info": player_character.description,
        },
    }


def render_night_action(game_engine, current_player):
    """Render effect of the Imp's ability during the night action phase."""
    log_info(f"Imp's ability: {current_player.player_status}.")
    player_character = current_player.character
    imp_status = "Już wykonałeś swoją nocną akcję!"
    player_list = []

    if current_player.is_night_action_done():
        log_info("Current player has already completed their night action.")
        screen_content = "imp_action_completed"
    elif game_engine.game_state.day == 0:
        log_info("This is the first night for the Imp")
        screen_content = "confirm_first_night_action"
        imp_status = "Pierwszej nocy IMP nie wykonuje akcji!"
    else:
        log_info("Rendering Imp's night action page.")
        screen_content = "select_player_to_kill"

        for player in game_engine.game_state.players:
            if player.alive == PlayerStatus.ALIVE:
                is_minion = (
                    ", Minion" if player.character.role_type == RoleType.MINION else ""
                )
                is_demon = (
                    ", Demon" if player.character.role_type == RoleType.DEMON else ""
                )
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
        for player in game_engine.game_state.players
        if player.character is not None
        and player.character.role_type == RoleType.MINION
    ]
    if not list_of_minions:
        list_of_minions = ["Brak Minionów w grze"]

    return {
        "screen": "night_imp",
        "character_data": {
            "role_name": player_character.name,
            "player_link": player_character.route,
            "player_image": player_character.image_path,
            "player_info": player_character.description,
            "screen_content": screen_content,
            "player_list": player_list,
            "imp_status": imp_status,
            "imp_extra_chars": ", ".join(list_of_extra_chars),
            "imp_minions": ", ".join(list_of_minions),
        },
    }


def render_deamon_replacement(game_engine, current_player):
    """Render page for Demon replacement if Imp has nominated themselves to die."""
    log_info("Imp has nominated himself to die, setting up for Demon replacement.")
    imp_status = (
        "\nWybrałeś siebie, więc jeden z Minionów prawdopodobnie zostanie Impem!"
    )
    player_character = current_player.character
    alive_minions = [
        player
        for player in game_engine.game_state.players
        if player.alive == PlayerStatus.ALIVE
        and player.character is not None
        and player.character.role_type == RoleType.MINION
    ]

    if len(alive_minions) == 1:
        game_engine.game_state.demon_replacement_candidate = alive_minions[0]
        log_info(
            "Only one alive Minion found. Auto-setting Demon replacement candidate: "
            f"{alive_minions[0].name}"
        )
        player_list = []
        screen_content = "confirm_replacement"
        imp_status = f"\nWybrałeś siebie. {alive_minions[0].name} zostanie nowym Impem."
    else:
        player_list = []
        for player in game_engine.game_state.players:
            if (
                player.alive == PlayerStatus.ALIVE
                and player.character is not None
                and player.character.role_type == RoleType.MINION
            ):
                player_list.append(
                    (
                        f"{player.name} - Minion (miejsce: {player.seat_no})",
                        player.client_id,
                    )
                )
        screen_content = "select_replacement"
        log_info(f"Player list for Imp's ability effect: {player_list}")

    list_of_extra_chars = [
        player.name for player in current_player.additional_characters
    ]
    list_of_minions = [
        player.name
        for player in game_engine.game_state.players
        if player.character is not None
        and player.character.role_type == RoleType.MINION
    ]
    if not list_of_minions:
        list_of_minions = ["Brak Minionów w grze"]

    return {
        "screen": "night_imp",
        "character_data": {
            "role_name": player_character.name,
            "player_link": player_character.route,
            "player_image": player_character.image_path,
            "player_info": player_character.description,
            "screen_content": screen_content,
            "player_list": player_list,
            "imp_status": imp_status,
            "imp_extra_chars": ", ".join(list_of_extra_chars),
            "imp_minions": ", ".join(list_of_minions),
        },
    }


def render_night_resolution(game_engine, current_player):
    """Render Imp's night resolution state."""
    log_info(f"Imp's ability: {current_player.player_status}.")
    player_character = current_player.character
    list_of_extra_chars = [
        player.name for player in current_player.additional_characters
    ]
    list_of_minions = [
        player.name
        for player in game_engine.game_state.players
        if player.character is not None
        and player.character.role_type == RoleType.MINION
    ]
    if not list_of_minions:
        list_of_minions = ["Brak Minionów w grze"]

    return {
        "screen": "night_imp",
        "character_data": {
            "role_name": player_character.name,
            "player_link": player_character.route,
            "player_image": player_character.image_path,
            "player_info": player_character.description,
            "screen_content": "imp_action_completed",
            "allow_imp_night_action": False,
            "player_list": [],
            "imp_status": "Nocna akcja została wykonana.",
            "imp_extra_chars": ", ".join(list_of_extra_chars),
            "imp_minions": ", ".join(list_of_minions),
        },
    }


# = = = = = = = = = = = = =  ABILITY EFFECTS = = = = = = = = = = = = =


def ability_setup(data):
    """Configure for the Imp's ability."""
    player, game_setup = (
        data["target"],
        data["game_setup"],
    )
    list_of_available_good_chars = game_setup.get_list_of_characters_by_type(
        [RoleType.TOWNSFOLK, RoleType.OUTSIDER], available_only=True
    )
    list_of_available_good_chars = [
        char for char in list_of_available_good_chars if char.character.name != "Pijak"
    ]  # Exclude Pijak from the list of available characters for Imp's ability setup
    log_info(
        f"Available good characters for Imp's ability setup: {[char.character.name for char in list_of_available_good_chars]}"
    )
    if len(list_of_available_good_chars) < 3:
        raise ValueError(
            "Not enough good characters available for Imp's ability setup."
        )
    random_good_chars = random.sample(list_of_available_good_chars, 3)
    player.additional_characters = random_good_chars
    player.additional_characters = [
        char.character for char in player.additional_characters
    ]
    for char in random_good_chars:
        char.assigned_in_play += 1
    log_info(
        f"Imp's ability setup: assigned additional characters to Imp: {[char.character.name for char in random_good_chars]}"
    )


def ability_callback_imp_kills(data):
    """Handle callback for the Imp's ability."""
    player_id, game_state, callback_data = (
        data["actor_id"],
        data["game_state"],
        data["callback_data"],
    )
    log_info(f"Imp's ability callback called with data: {callback_data}")
    game_state.set_nominated_by_imp_to_die(callback_data.get("selected_player"))
    player = game_state.get_player_by_client_id(player_id)
    nominated_player = game_state.nominated_by_imp_to_die
    no_of_alive_minions = len(
        [
            player
            for player in game_state.players
            if player.character is not None
            and player.character.role_type == RoleType.MINION
            and player.alive == PlayerStatus.ALIVE
        ]
    )

    if no_of_alive_minions == 0:
        log_info("No alive Minions found. IMP successfully killed himself.")

    elif nominated_player and nominated_player.client_id == player.client_id:
        log_info("Imp has nominated himself to die, setting up for Demon replacement.")
        event = Event(
            name="imp_suicide_selected",
            actor_id=player.client_id,
            priority=50,
        )
        return [event]
    event = Event(
        name="confirm_night_action",
        actor_id=player.client_id,
        priority=50,
    )
    return [event]


def ability_callback_suicide(data):
    """Handle callback for the Imp's suicide."""
    log_info(f"Imp's ability callback called with data: {data}")
    player_id, game_state, callback_data = (
        data["actor_id"],
        data["game_state"],
        data["callback_data"],
    )
    player = game_state.get_player_by_client_id(player_id)
    selected_player = game_state.get_player_by_client_id(
        callback_data.get("selected_player")
    )
    game_state.set_demon_replacement_candidate(selected_player)
    event = Event(
        name="confirm_night_action",
        actor_id=player.client_id,
        priority=50,
    )
    return [event]


def ability_night_resolution_original(data):
    """Handle callback for the Imp's ability."""
    log_info(f"Imp's ability callback called with data: {data}")
    player, game_state = (
        data["target"],
        data["game_state"],
    )

    player_to_die = game_state.nominated_by_imp_to_die

    if player_to_die is None:
        log_info("No player nominated by Imp to die.")
        return []

    if player.client_id != player_to_die.client_id:
        log_info(
            f"Player nominated by Imp to die: {player_to_die.name if player_to_die else 'None'}"
        )
        player_to_die.imp_kills_player()
    elif game_state.demon_replacement_candidate is None:
        log_info("Imp killed himself, but there is no replacement candidate.")
        player.imp_kills_player()
    else:
        tmp_character = game_state.demon_replacement_candidate.character
        game_state.demon_replacement_candidate.character = player.character
        game_state.demon_replacement_candidate.additional_characters = (
            player.additional_characters
        )
        player.imp_kills_player()
        player.additional_characters = []
        player.character = tmp_character
        log_info(
            f"Player {player.name} dies and new Demon is: {game_state.demon_replacement_candidate.name}"
        )
    return []

    # try:
    #     selected_json = json.loads(data.get("selected_json", "[]"))
    # except json.JSONDecodeError:
    #     selected_json = []

    # if not selected_json:
    #     log_info("No player selected in Imp's ability callback.")
    #     return effect_night_all_players(ct_game)

    # current_player = ct_game.game_state.get_current_player()
    # player_selected = ct_game.game_state.get_player_by_client_id(selected_json[0])
    # current_player.confirm_admin_action()

    # if player_selected is None:
    #     log_info("Selected player for Imp's ability callback not found.")
    #     return effect_night_all_players(ct_game)

    # if replace_demon:
    #     log_info(f"Player selected for Demon replacement: {player_selected.name}")
    #     ct_game.game_state.demon_replacement_candidate = player_selected
    #     return effect_night_all_players(ct_game)

    # ct_game.game_state.nominated_by_imp_to_die = player_selected

    # log_info(f"Player nominated by Imp to die: {player_selected.name}")

    # if current_player.poisoned:
    #     log_info("Current player is poisoned, skipping Imp's night action effect.")
    #     ct_game.game_state.nominated_by_imp_to_die = None

    # if player_selected.client_id == current_player.client_id:

    # return effect_night_all_players(ct_game)


def ability_night_resolution_fake(data):
    log_info(f"Imp's fake ability callback called with data: {data}")
    player, game_state, game_setup = (
        data["target"],
        data["game_state"],
        data["game_setup"],
    )
    log_info(
        "This is a fake night resolution for the Imp, no actual game state changes will occur."
    )
    return []


ability = Ability(
    setup=DualEffect(
        original=ability_setup,
    ),
    night_resolution=DualEffect(
        original=ability_night_resolution_original,
        fake=ability_night_resolution_fake,
    ),
)
ability.callback_imp_kills = DualEffect(
    original=ability_callback_imp_kills,
)
ability.callback_suicide = DualEffect(
    original=ability_callback_suicide,
)


render_page = RenderPage(
    introduction=DualEffect(
        original=render_introduction,
    ),
    night_action=DualEffect(
        original=render_night_action,
        fake=render_night_action,
    ),
    night_resolution=DualEffect(
        original=render_night_resolution,
        fake=render_night_resolution,
    ),
)
render_page.demon_replacement = DualEffect(
    original=render_deamon_replacement,
)


class ImpCharacter(Character):
    """Class representing the Imp character."""

    def __init__(self):
        """Initialize the Imp character."""

        super().__init__(
            name="Imp",
            role_type=RoleType.DEMON,
            ability=ability,
            render_page=render_page,
            image_path="imp.png",
            route="imp",
        )

        self.description = (
            "Każdej nocy, wybierz gracza: ten gracz umiera. "
            "Jeśli w ten sposób zabijesz samego siebie, jeden z Minionów "
            "staje się Impem. Imp zabija jednego gracza każdej nocy."
        )
