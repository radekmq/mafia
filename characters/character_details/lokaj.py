from characters.character import Ability, Character, DualEffect, RenderPage, RoleType
from game_events import Event
from logger import log_info
from player import PlayerStatus, PlayerVoteStatus

# = = = = = = = = = = = = =  RENDER PAGE = = = = = = = = = = = = =


def render_introduction(game_engine, current_player):
    """Render effect of the Lokajs's ability during the introduction phase."""
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
    """Render effect of the Lokaj's ability during the night action phase."""
    log_info("Lokaj's ability effect for night_minion_action called.")
    player_character = current_player.character

    lokaj_status = "Już wykonałeś swoją nocną akcję!"
    if (
        current_player.is_night_action_done()
        or current_player.alive == PlayerStatus.DEAD
    ):
        log_info("Current player has already completed their night action or is dead.")
        screen_content = "lokaj_action_completed"
        lokaj_status = "Wykonałeś już swoją nocną akcję lub ona nie działa."
    else:
        log_info("Rendering Lokaj's night action page.")
        screen_content = "select_player"
        lokaj_status = "Wybierz gracza, któremu chcesz służyć kolejnego dnia."

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
    log_info(f"Player list for Lokaj's ability effect: {player_list}")

    return {
        "screen": "night_lokaj",
        "character_data": {
            "role_name": player_character.name,
            "player_link": player_character.route,
            "player_image": player_character.image_path,
            "player_info": player_character.description,
            "screen_content": screen_content,
            "player_list": player_list,
            "lokaj_status": lokaj_status,
        },
    }


def render_night_resolution(game_engine, current_player):
    """Effect of the Lokaj's ability during night_all_players_action state."""
    log_info(f"Lokaj's ability: {current_player.player_status}.")
    player_character = current_player.character
    player_status = "Nie wybrałeś jeszcze Pana."
    if current_player.butlers_master is not None:
        master_player = game_engine.game_state.get_player_by_client_id(
            current_player.butlers_master
        )
        if master_player is not None:
            player_status = f"Zobowiązałeś się do służby dla Pana: {master_player.name}"
    if current_player.alive == PlayerStatus.DEAD:
        player_status = "Niestety Twoja zdolność już nie działa."

    return {
        "screen": "night_lokaj",
        "character_data": {
            "role_name": player_character.name,
            "player_link": player_character.route,
            "player_image": player_character.image_path,
            "player_info": player_character.description,
            "screen_content": "lokaj_action_completed",
            "player_list": [],
            "lokaj_status": player_status,
        },
    }


# = = = = = = = = = = = = =  ABILITY EFFECTS = = = = = = = = = = = = =


def ability_setup(data):
    """Configure for the Lokaj's ability."""
    log_info("Lokaj does not need setup.")
    player, game_state, game_setup = (
        data["target"],
        data["game_state"],
        data["game_setup"],
    )
    player.butlers_master = None


def ability_callback_butler(data):
    """Handle callback for the Lokaj's ability."""
    player, game_state, game_setup, callback_data = (
        data["actor"],
        data["game_state"],
        data["game_setup"],
        data["callback_data"],
    )
    log_info(f"Lokaj's ability callback called with data: {callback_data}")
    player.butlers_master = callback_data.get("selected_player")

    event = Event(
        name="confirm_night_action",
        actor_id=player.client_id,
        priority=50,
    )
    return [event]


ability = Ability(
    setup=DualEffect(
        original=ability_setup,
    ),
)
ability.callback_butler = DualEffect(
    original=ability_callback_butler,
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


class LokajCharacter(Character):
    """Class representing the Lokaj character."""

    def __init__(self):
        """Initialize the Lokaj character."""

        super().__init__(
            name="Lokaj",
            role_type=RoleType.OUTSIDER,
            ability=ability,
            render_page=render_page,
            image_path="lokaj.png",
            route="lokaj",
        )

        self.description = (
            "Każdej nocy wybierz gracza (nie siebie): jutro możesz głosować tylko wtedy, "
            "gdy on również głosuje."
            "Lokaj może głosować tylko wtedy, gdy jego Pan (inny gracz) również głosuje."
        )

    def can_vote_yes(self, player, game_state):
        """Determine if the Lokaj can vote YES."""
        if player.butlers_master is None:
            log_info(f"Lokaj {player.name} has no master and cannot vote YES.")
            return False

        master_player = game_state.get_player_by_client_id(player.butlers_master)
        if (
            master_player
            and master_player.alive == PlayerStatus.ALIVE
            and master_player.vote_status == PlayerVoteStatus.VOTED_YES
        ):
            log_info(
                f"Lokaj {player.name} can vote YES because their master {master_player.name} is alive and has voted YES."
            )
            return True
        else:
            log_info(
                f"Lokaj {player.name} cannot vote YES because their master is not alive or has not voted YES."
            )
            return False
