from characters.character import Ability, Character, DualEffect, RenderPage, RoleType
from game_events import Event
from logger import log_info
from player import PlayerStatus

# = = = = = = = = = = = = =  RENDER PAGE = = = = = = = = = = = = =


def render_introduction(game_engine, current_player):
    """Render effect of the Truciciels's ability during the introduction phase."""
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
    """Render effect of the Truciciel's ability during the night action phase."""
    log_info("Truciciel's ability effect for night_minion_action called.")
    player_character = current_player.character

    truciciel_status = "Już wykonałeś swoją nocną akcję!"
    if (
        current_player.is_night_action_done()
        or current_player.alive == PlayerStatus.DEAD
    ):
        log_info("Current player has already completed their night action or is dead.")
        screen_content = "truciciel_action_completed"
        truciciel_status = "Potwierdziłeś swoją nocną akcję lub ona nie działa."
    else:
        log_info("Rendering Truciciel's night action page.")
        screen_content = "select_player_to_poison"
        truciciel_status = "Wybierz gracza, którego chcesz otruc tej nocy."

    player_list = []
    if screen_content == "select_player_to_poison":
        for player in game_engine.game_state.players:
            if player.alive == PlayerStatus.ALIVE:
                if player.character is None:
                    continue
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
    log_info(f"Player list for Truciciel's ability effect: {player_list}")

    list_of_minions = [
        player.name
        for player in game_engine.game_state.players
        if player.character is not None
        and player.character.role_type == RoleType.MINION
    ]
    if not list_of_minions:
        list_of_minions = ["Brak Minionów w grze"]

    return {
        "screen": "night_truciciel",
        "character_data": {
            "role_name": player_character.name,
            "player_link": player_character.route,
            "player_image": player_character.image_path,
            "player_info": player_character.description,
            "screen_content": screen_content,
            "player_list": player_list,
            "truciciel_status": truciciel_status,
            "truciciel_minions": ", ".join(list_of_minions),
        },
    }


def render_night_resolution(game_engine, current_player):
    """Effect of the Truciciel's ability during night_all_players_action state."""
    log_info(f"Truciciel's ability: {current_player.player_status}.")
    player_character = current_player.character
    list_of_minions = [
        player.name
        for player in game_engine.game_state.players
        if player.character is not None
        and player.character.role_type == RoleType.MINION
    ]
    if not list_of_minions:
        list_of_minions = ["Brak Minionów w grze"]
    player_status = "Zleciłeś otrucie gracza. Nocna akcja została wykonana."
    if current_player.alive == PlayerStatus.DEAD:
        player_status = "Niestety Twoja zdolność już nie działa."

    return {
        "screen": "night_truciciel",
        "character_data": {
            "role_name": player_character.name,
            "player_link": player_character.route,
            "player_image": player_character.image_path,
            "player_info": player_character.description,
            "screen_content": "truciciel_action_completed",
            "player_list": [],
            "truciciel_status": player_status,
            "truciciel_minions": ", ".join(list_of_minions),
        },
    }


# = = = = = = = = = = = = =  ABILITY EFFECTS = = = = = = = = = = = = =


def ability_setup(data):
    """Configure for the Truciciel's ability."""
    log_info("Truciciel does not need setup.")


def ability_callback_poison(data):
    """Handle callback for the Truciciel's ability."""
    player_id, game_state, game_setup, callback_data = (
        data["actor_id"],
        data["game_state"],
        data["game_setup"],
        data["callback_data"],
    )
    log_info(f"Truciciel's ability callback called with data: {callback_data}")
    game_state.set_nominated_to_poison(callback_data.get("selected_player"))
    player = game_state.get_player_by_client_id(player_id)
    event = Event(
        name="confirm_night_action",
        actor_id=player.client_id,
        priority=50,
    )
    return [event]


def ability_night_resolution_original(data):
    """Handle callback for the Truciciel's ability."""
    log_info(f"Truciciel's ability callback called with data: {data}")
    player, game_state, game_setup = (
        data["target"],
        data["game_state"],
        data["game_setup"],
    )

    player_to_poison = game_state.nominated_to_poison

    if player_to_poison is None:
        log_info("No player nominated to poison.")
        return []

    player_to_poison.set_poisoned(True)
    return []


def ability_night_resolution_fake(data):
    log_info(f"Truciciel's fake ability callback called with data: {data}")
    player, game_state, game_setup = (
        data["target"],
        data["game_state"],
        data["game_setup"],
    )
    log_info(
        "This is a fake night resolution for the Truciciel, no actual game state changes will occur."
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
ability.callback_poison = DualEffect(
    original=ability_callback_poison,
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


class TrucicielCharacter(Character):
    """Class representing the Truciciel character."""

    def __init__(self):
        """Initialize the Truciciel character."""

        super().__init__(
            name="Truciciel",
            role_type=RoleType.MINION,
            ability=ability,
            render_page=render_page,
            image_path="truciciel.png",
            route="truciciel",
        )

        self.description = (
            "Każdej nocy wybierz gracza: ten gracz jest zatruty tej nocy "
            "oraz następnego dnia."
        )
