import random

from characters.character import Ability, Character, DualEffect, RenderPage, RoleType
from game_events import Event
from logger import log_info
from player import PlayerStatus

# = = = = = = = = = = = = =  RENDER PAGE = = = = = = = = = = = = =


def render_introduction(game_engine, current_player):
    """Render effect of the Jasnowidzs's ability during the introduction phase."""
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
    """Render effect of the Jasnowidz's ability during the night action phase."""
    log_info("Jasnowidz's ability effect for night_minion_action called.")
    player_character = current_player.character

    jasnowidz_status = "Już wykonałeś swoją nocną akcję!"
    if (
        current_player.is_night_action_done()
        or current_player.alive == PlayerStatus.DEAD
    ):
        log_info("Current player has already completed their night action or is dead.")
        screen_content = "jasnowidz_action_completed"
        jasnowidz_status = "Potwierdziłeś swoją nocną akcję lub ona nie działa."
    else:
        log_info("Rendering Jasnowidz's night action page.")
        screen_content = "select_player_to_see"
        jasnowidz_status = "Wybierz gracza, którego rolę chcesz poznać."

    player_list = []
    if screen_content == "select_player_to_see":
        for player in game_engine.game_state.players:
            player_list.append(
                (
                    f"{player.name} (miejsce: {player.seat_no})",
                    player.client_id,
                )
            )
    log_info(f"Player list for Jasnowidz's ability effect: {player_list}")

    return {
        "screen": "night_jasnowidz",
        "character_data": {
            "role_name": player_character.name,
            "player_link": player_character.route,
            "player_image": player_character.image_path,
            "player_info": player_character.description,
            "screen_content": screen_content,
            "player_list": player_list,
            "jasnowidz_status": jasnowidz_status,
        },
    }


def render_night_resolution(game_engine, current_player):
    """Effect of the Jasnowidz's ability during night_all_players_action state."""
    log_info(f"Jasnowidz's ability: {current_player.player_status}.")
    player_character = current_player.character

    if (
        current_player.alive == PlayerStatus.DEAD
        and game_engine.game_state.nominated_by_imp_to_die is not current_player
    ):
        player_status = "Niestety Twoja zdolność już nie działa."
    else:
        player_status = (
            current_player.jasnowidz_status
            if hasattr(current_player, "jasnowidz_status")
            else "Brak informacji o wyniku zdolności jasnowidza."
        )

    return {
        "screen": "night_jasnowidz",
        "character_data": {
            "role_name": player_character.name,
            "player_link": player_character.route,
            "player_image": player_character.image_path,
            "player_info": player_character.description,
            "screen_content": "jasnowidz_action_completed",
            "player_list": [],
            "jasnowidz_status": player_status,
        },
    }


# = = = = = = = = = = = = =  ABILITY EFFECTS = = = = = = = = = = = = =


def ability_setup(data):
    """Configure for the Jasnowidz's ability."""
    log_info("Jasnowidz does not need setup.")
    player, game_state, game_setup = (
        data["target"],
        data["game_state"],
        data["game_setup"],
    )
    player.character.cached_fake_night_result = {}


def ability_callback_i_see_you(data):
    """Handle callback for the Jasnowidz's ability."""
    player, game_state, game_setup, callback_data = (
        data["target"],
        data["game_state"],
        data["game_setup"],
        data["callback_data"],
    )
    log_info(f"Jasnowidz's ability callback called with data: {callback_data}")
    player.character.selected_players_to_see = callback_data.get("selected_players")

    event = Event(
        name="confirm_night_action",
        actor_id=player.client_id,
        priority=50,
    )
    return [event]


def ability_night_resolution_original(data):
    """Handle callback for the Jasnowidz's ability."""
    log_info(f"Jasnowidz's ability callback called with data: {data}")
    player, game_state, game_setup = (
        data["target"],
        data["game_state"],
        data["game_setup"],
    )

    if (
        hasattr(player.character, "selected_players_to_see")
        and player.character.selected_players_to_see
    ):
        selected_players = player.character.selected_players_to_see
        log_info(f"Jasnowidz selected players to see: {selected_players}")

        is_deamon_found = False
        for selected_player_id in selected_players:
            target_player = game_state.get_player_by_client_id(selected_player_id)
            if target_player.character.role_type == RoleType.DEMON:
                player.jasnowidz_status = "Wiesz, że wśród wskazanych przez Ciebie wybranych graczy jest Demon."
                is_deamon_found = True
                break

        if is_deamon_found:
            player.jasnowidz_status = (
                "Wiesz, że wśród wskazanych przez Ciebie graczy jest Demon."
            )
            player.character.useful_yes_results += 1
        else:
            player.jasnowidz_status = (
                "Nie ma Demona wśród wskazanych przez Ciebie graczy."
            )
            player.character.confirmed_no_results += 1
    else:
        player.jasnowidz_status = "Żadna informacja nie jest dostępna dla jasnowidza."

    player.character.selected_players_to_see = None
    return []


def ability_night_resolution_fake(data):
    log_info(f"Jasnowidz's fake ability callback called with data: {data}")
    player, game_state, game_setup = (
        data["target"],
        data["game_state"],
        data["game_setup"],
    )

    if (
        hasattr(player.character, "selected_players_to_see")
        and player.character.selected_players_to_see
    ):
        selected_players = player.character.selected_players_to_see
        log_info(f"Jasnowidz selected players to see: {selected_players}")

        random_result = player.character.cached_fake_night_result.get(
            frozenset(selected_players)
        )
        if random_result is not None:
            log_info(
                f"Using cached fake night result for selected players: {random_result}"
            )
        else:
            random_result = random.choice([True, False])
            player.character.cached_fake_night_result[
                frozenset(selected_players)
            ] = random_result

        if random_result:
            player.jasnowidz_status = (
                "Wiesz, że wśród wskazanych przez Ciebie graczy jest Demon."
            )
        else:
            player.jasnowidz_status = (
                "Nie ma Demona wśród wskazanych przez Ciebie graczy."
            )
    else:
        player.jasnowidz_status = "Żadna informacja nie jest dostępna dla jasnowidza."

    player.character.selected_players_to_see = None
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
ability.callback_i_see_you = DualEffect(
    original=ability_callback_i_see_you,
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


class JasnowidzCharacter(Character):
    """Class representing the Jasnowidz character."""

    def __init__(self):
        """Initialize the Jasnowidz character."""

        super().__init__(
            name="Jasnowidz",
            role_type=RoleType.TOWNSFOLK,
            ability=ability,
            render_page=render_page,
            image_path="jasnowidz.png",
            route="jasnowidz",
        )

        self.description = (
            (
                "Po każdej nocy wybierz 2 graczy: dowiadujesz się, "
                "czy którykolwiek z nich jest Demonem. Jasnowidz dowiaduje się, "
                "czy którykolwiek z dwóch graczy jest Demonem."
            ),
        )
        self.useful_yes_results = 0
        self.confirmed_no_results = 0

    def evaluate_knowledge_score(self):
        score = 0
        # liczba trafień zawężających demona
        score += self.useful_yes_results * 2
        # liczba potwierdzonych NO
        score += self.confirmed_no_results * 1

        return score
