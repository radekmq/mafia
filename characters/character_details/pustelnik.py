from characters.character import Ability, Character, DualEffect, RenderPage, RoleType
from logger import log_info

# = = = = = = = = = = = = =  RENDER PAGE = = = = = = = = = = = = =


def render_introduction(game_engine, current_player):
    """Render effect of the Swiety's ability during the introduction phase."""
    log_info("Get data for Swiety introduction.")
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
    """Effect of the Swiety's ability during night_all_players_action state."""
    log_info("Get data for Swiety night action.")

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
    """Effect of the Swiety's ability during night_all_players_action state."""
    log_info("Get data for Swiety night resolution.")
    player_character = current_player.character

    return {
        "screen": "night_basic",
        "character_data": {
            "role_name": player_character.name,
            "player_link": player_character.route,
            "player_image": player_character.image_path,
            "player_info": player_character.description,
            "player_status": "Święty nie wykonuje specjalnej akcji w nocy.",
            "screen_content": "action_completed",
        },
    }

    # = = = = = = = = = = = = =  ABILITY EFFECTS = = = = = = = = = = = = =

    """Configure for the Swiety's ability."""


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


class SwietyCharacter(Character):
    """Class representing the Swiety character."""

    def __init__(self):
        """Initialize the Swiety character."""

        super().__init__(
            name="Swiety",
            role_type=RoleType.OUTSIDER,
            ability=ability,
            render_page=render_page,
            image_path="swiety.png",
            route="swiety",
        )

        self.description = (
            (
                "Jeśli zostaniesz stracony w wyniku egzekucji, twoja drużyna przegrywa. "
                "Święty (Saint) kończy grę porażką swojej drużyny, jeśli zostanie stracony."
            ),
        )

    def game_over_conditions(self, game_state) -> bool:
        """Check game over conditions for the Swiety character."""
        log_info("Checking game over conditions for Swiety.")

        swiety_player = next(
            (player for player in game_state.players if player.character == self), None
        )

        if swiety_player is None:
            log_info("Swiety is not in the game, skipping game over check.")

        elif swiety_player.is_player_executed():
            log_info("Swiety has been executed. Game over condition met.")
            game_state.winning_team = "Źli (Minionki + Demon)"
            game_state.set_game_over_conditions_met(True)

        else:
            log_info("Swiety has not been executed. Game over condition not met.")

        return []
