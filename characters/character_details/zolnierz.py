from characters.character import Ability, Character, DualEffect, RenderPage, RoleType
from logger import log_info
from player import PlayerStatus

# = = = = = = = = = = = = =  RENDER PAGE = = = = = = = = = = = = =


def render_introduction(game_engine, current_player):
    """Render effect of the Zolnierz's ability during the introduction phase."""
    log_info("Get data for Zolnierz introduction.")
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
    """Effect of the Zolnierz's ability during night_all_players_action state."""
    log_info("Get data for Zolnierz night action.")

    screen_content = "confirm_night_action"
    player_status = "Potwierdź swoją nocną akcję."
    if current_player.is_night_action_done():
        log_info("Current player has already completed their night action.")
        screen_content = "action_completed"
        player_status = "Potwierdziłeś swoją nocną akcję."
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
    """Effect of the Zolnierz's ability during night_all_players_action state."""
    log_info("Get data for Zolnierz night resolution.")
    player_character = current_player.character

    return {
        "screen": "night_basic",
        "character_data": {
            "role_name": player_character.name,
            "player_link": player_character.route,
            "player_image": player_character.image_path,
            "player_info": player_character.description,
            "player_status": "Żołnierz nie wykonuje specjalnej akcji w nocy.",
            "screen_content": "action_completed",
        },
    }


# = = = = = = = = = = = = =  ABILITY EFFECTS = = = = = = = = = = = = =


def ability_setup(data):
    """Configure for the Zolnierz's ability."""
    log_info("Zolnierz setup.")
    player = data["target"]
    player.set_protected(True)


def ability_night_resolution_original(data):
    """Handle callback for the Zolnierz's ability."""
    log_info(f"Zolnierz's ability callback called with data: {data}")
    player = data["target"]
    player.set_protected(True)


def ability_night_resolution_fake(data):
    log_info(f"Zolnierz's fake ability callback called with data: {data}")
    player = data["target"]
    player.set_protected(False)


ability = Ability(
    setup=DualEffect(
        original=ability_setup,
    ),
    night_resolution=DualEffect(
        original=ability_night_resolution_original,
        fake=ability_night_resolution_fake,
    ),
)

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


class ZolnierzCharacter(Character):
    """Class representing the Zolnierz character."""

    def __init__(self):
        """Initialize the Zolnierz character."""

        super().__init__(
            name="Zolnierz",
            role_type=RoleType.TOWNSFOLK,
            ability=ability,
            render_page=render_page,
            image_path="zolnierz.png",
            route="zolnierz",
        )

        self.description = (
            (
                "Jesteś bezpieczny przed Demonem. "
                "Żołnierz (Soldier) nie może zostać zabity przez Demona."
            ),
        )

    def evaluate_knowledge_score(self, player) -> float:
        """Evaluate knowledge score based on the information they have."""
        if player.alive == PlayerStatus.DEAD:
            return 0
        if player.poisoned:
            return 1
        return 2
