from characters.character import Ability, Character, DualEffect, RenderPage, RoleType
from logger import log_info

# = = = = = = = = = = = = =  RENDER PAGE = = = = = = = = = = = = =


def render_introduction(game_engine, current_player):
    """Render effect of the Pustelnik's ability during the introduction phase."""
    log_info("Get data for Pustelnik introduction.")
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
    """Effect of the Pustelnik's ability during night_all_players_action state."""
    log_info("Get data for Pustelnik night action.")

    screen_content = "confirm_night_action"
    player_status = "Potwierdź swoją nocną akcję."
    if current_player.is_night_action_done() or not current_player.is_alive():
        log_info("Current player has already completed their night action or is dead.")
        screen_content = "action_completed"
        player_status = "Potwierdziłeś swoją nocną akcję lub ona nie działa."
    player_character = current_player.character

    return {
        "screen": "night_basic",
        "character_data": {
            "role_name": player_character.name,
            "player_link": player_character.route,
            "player_image": player_character.image_path,
            "player_info": player_character.description,
            "player_status": player_status,
            "screen_content": screen_content,
        },
    }


def render_night_resolution(game_engine, current_player):
    """Effect of the Pustelnik's ability during night_all_players_action state."""
    log_info("Get data for Pustelnik night resolution.")
    player_character = current_player.character

    return {
        "screen": "night_basic",
        "character_data": {
            "role_name": player_character.name,
            "player_link": player_character.route,
            "player_image": player_character.image_path,
            "player_info": player_character.description,
            "player_status": "Pustelnik nie wykonuje specjalnej akcji w nocy.",
            "screen_content": "action_completed",
        },
    }

    # = = = = = = = = = = = = =  ABILITY EFFECTS = = = = = = = = = = = = =

    """Configure for the Pustelnik's ability."""


ability = Ability()

render_page = RenderPage(
    introduction=DualEffect(
        original=render_introduction,
        fake=render_introduction,
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


class PustelnikCharacter(Character):
    """Class representing the Pustelnik character."""

    def __init__(self):
        """Initialize the Pustelnik character."""

        super().__init__(
            name="Pustelnik",
            role_type=RoleType.OUTSIDER,
            ability=ability,
            render_page=render_page,
            image_path="pustelnik.png",
            route="pustelnik",
        )

        self.description = (
            (
                "Możesz być rozpoznawany jako zły oraz jako Minion lub Demon, nawet jeśli jesteś martwy. "
                "Pustelnik może wyglądać na złą postać, ale w rzeczywistości jest dobry."
            ),
        )

    def set_recluse_heuristic(self, heuristic):
        self.heuristic = heuristic
