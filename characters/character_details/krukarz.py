import random

from characters.character import Ability, Character, DualEffect, RenderPage, RoleType
from game_events import Event
from logger import log_info
from player import PlayerStatus

# = = = = = = = = = = = = =  RENDER PAGE = = = = = = = = = = = = =


def render_introduction(game_engine, current_player):
    """Render effect of the Krukarz's ability during the introduction phase."""
    log_info("Get data for Krukarz introduction.")
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
    """Render effect of the Krukarz's ability during the night action phase."""
    log_info("Krukarz's ability effect for night_minion_action called.")
    player_character = current_player.character

    krukarz_status = "Już wykonałeś swoją nocną akcję!"
    if current_player.is_night_action_done() or not current_player.is_alive():
        log_info("Current player has already completed their night action or is dead.")
        screen_content = "krukarz_action_completed"
        krukarz_status = "Wykonałeś już swoją nocną akcję lub ona nie działa."
    else:
        log_info("Rendering Krukarz's night action page.")
        screen_content = "select_player"
        krukarz_status = "Wybierz gracza, którego rolę w grze chcesz poznać (tylko jeżeli zostaniesz wyeliminowany tej nocy)."

    player_list = []
    if screen_content == "select_player":
        for player in game_engine.game_state.players:
            if player.client_id == current_player.client_id or player.character is None:
                continue
            player_list.append(
                (
                    f"{player.name} (miejsce: {player.seat_no})",
                    player.client_id,
                )
            )
    log_info(f"Player list for Krukarz's ability effect: {player_list}")

    return {
        "screen": "night_krukarz",
        "character_data": {
            "role_name": player_character.name,
            "player_link": player_character.route,
            "player_image": player_character.image_path,
            "player_info": player_character.description,
            "screen_content": screen_content,
            "player_list": player_list,
            "krukarz_status": krukarz_status,
        },
    }


def render_night_resolution(game_engine, current_player):
    """Effect of the Krukarz's ability during night_all_players_action state."""
    log_info("Get data for Krukarz night resolution.")
    player_character = current_player.character

    return {
        "screen": "night_basic",
        "character_data": {
            "role_name": player_character.name,
            "player_link": player_character.route,
            "player_image": player_character.image_path,
            "player_info": player_character.description,
            "player_status": current_player.player_status,
            "screen_content": "action_completed",
        },
    }


# = = = = = = = = = = = = =  ABILITY EFFECTS = = = = = = = = = = = = =


def ability_setup(data):
    """Configure for the Krukarz's ability."""
    log_info("Setting up Krukarz's ability.")
    player, game_setup = (
        data["target"],
        data["game_setup"],
    )
    player.chosen_by_krukarz = None


def ability_callback_krukarz(data):
    """Handle callback for the Krukarz's ability."""
    player, game_state, callback_data = (
        data["actor"],
        data["game_state"],
        data["callback_data"],
    )
    log_info(f"Krukarz's ability callback called with data: {callback_data}")
    player.chosen_by_krukarz = game_state.get_player_by_client_id(
        callback_data.get("selected_player")
    )

    event = Event(
        name="confirm_night_action",
        actor_id=player.client_id,
        priority=50,
    )
    return [event]


def ability_night_resolution_original(data):
    """Handle callback for the Krukarz's ability."""
    log_info(f"Krukarz's ability callback called with data: {data}")

    player, game_state = (
        data["target"],
        data["game_state"],
    )

    player.player_status = "Krukarz nie otrzymał żadnej informacji, ponieważ nie został wyeliminowany tej nocy."
    log_info(
        f"Krukarz knows, that IMP eliminated this night: {game_state.nominated_by_imp_to_die.name if game_state.nominated_by_imp_to_die else 'None'}"
    )

    if (
        game_state.nominated_by_imp_to_die is not player
        or player.alive != PlayerStatus.DEAD
    ):
        log_info("Krukarz was not eliminated by the Imp. No information is revealed.")
        return

    if player.chosen_by_krukarz is None:
        log_info("Krukarz did not choose any player to learn about.")
        return

    log_info(f"Krukarz's chosen player: {player.chosen_by_krukarz.name}")

    if player.chosen_by_krukarz.character is None:
        log_info("Chosen player not found or has no character.")
        return

    revealed_role_name = player.chosen_by_krukarz.character.name
    player.player_status = f"Krukarz wie, że postać gracza {player.chosen_by_krukarz.name} to: {revealed_role_name}."
    player.character.has_received_information = True
    log_info(
        f"Krukarz learns that {player.chosen_by_krukarz.name} is {revealed_role_name}."
    )


def ability_night_resolution_fake(data):
    """Handle fake callback for the Krukarz's ability."""
    log_info(f"Krukarz's fake ability callback called with data: {data}")

    player, game_state, game_setup = (
        data["target"],
        data["game_state"],
        data["game_setup"],
    )

    player.player_status = "Krukarz nie otrzymał żadnej informacji, ponieważ nie został wyeliminowany tej nocy."

    if game_state.nominated_by_imp_to_die is not player or player.is_alive():
        log_info(
            "Krukarz was not eliminated by the Imp. No fake information is revealed."
        )
        return

    if player.chosen_by_krukarz is None:
        log_info("Krukarz did not choose any player to learn about.")
        player.player_status = (
            " Krukarz nie wybrał żadnego gracza, o którym chciałby się dowiedzieć."
        )
        return

    all_characters = game_setup.get_dict_of_characters()
    available_characters = [
        character
        for characters in all_characters.values()
        for character in characters
        if character.route != player.chosen_by_krukarz.character.route
        and character.route != player.character.route
    ]
    log_info(
        f"All characters available for Krukarz: {[char.name for char in available_characters]}"
    )

    if not available_characters:
        log_info("No available fake characters for Krukarz.")
        return

    shown_character = random.choice(available_characters)

    chosen_player_name = (
        player.chosen_by_krukarz.name
        if player.chosen_by_krukarz is not None
        else "brak wyboru"
    )

    player.player_status = f"Krukarz wie, że postać gracza {player.chosen_by_krukarz.name} to: {shown_character.name}."
    player.character.has_received_information = True
    log_info(
        f"Krukarz receives fake info: {chosen_player_name} appears as {shown_character.name}."
    )


ability = Ability(
    setup=DualEffect(
        original=ability_setup,
        fake=ability_setup,
    ),
    night_resolution=DualEffect(
        original=ability_night_resolution_original,
        fake=ability_night_resolution_fake,
    ),
)
ability.callback_krukarz = DualEffect(
    original=ability_callback_krukarz,
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


class KrukarzCharacter(Character):
    """Class representing the Krukarz character."""

    def __init__(self):
        """Initialize the Krukarz character."""

        super().__init__(
            name="Krukarz",
            role_type=RoleType.TOWNSFOLK,
            ability=ability,
            render_page=render_page,
            image_path="krukarz.png",
            route="krukarz",
        )

        self.description = (
            (
                "Jeśli umrzesz w nocy, zostajesz obudzony, aby wybrać gracza: poznajesz jego postać. "
                "Jeśli Krukarz umrze w nocy, może poznać postać jednego gracza."
            ),
        )
        self.has_received_information = False

    def evaluate_knowledge_score(self, _) -> float:
        """Evaluate knowledge score based on the information they have."""
        if self.has_received_information:
            return 3.0
        return 0
