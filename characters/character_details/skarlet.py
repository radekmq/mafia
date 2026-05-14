from characters.character import Ability, Character, DualEffect, RenderPage, RoleType
from logger import log_info

# = = = = = = = = = = = = =  RENDER PAGE = = = = = = = = = = = = =


def render_introduction(game_engine, current_player):
    """Render effect of the Skarlet's ability during the introduction phase."""
    log_info("Get data for Skarlet introduction.")
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
    """Effect of the Skarlet's ability during night_all_players_action state."""
    log_info("Get data for Skarlet night action.")

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
    """Effect of the Skarlet's ability during night_all_players_action state."""
    log_info("Get data for Skarlet night resolution.")
    player_character = current_player.character

    return {
        "screen": "night_basic",
        "character_data": {
            "role_name": player_character.name,
            "player_link": player_character.route,
            "player_image": player_character.image_path,
            "player_info": player_character.description,
            "player_status": "Skarlet nie wykonuje specjalnej akcji w nocy.",
            "screen_content": "action_completed",
        },
    }

    # = = = = = = = = = = = = =  ABILITY EFFECTS = = = = = = = = = = = = =

    """Configure for the Skarlet's ability."""


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


class SkarletCharacter(Character):
    """Class representing the Skarlet character."""

    def __init__(self):
        """Initialize the Skarlet character."""

        super().__init__(
            name="Skarlet",
            role_type=RoleType.MINION,
            ability=ability,
            render_page=render_page,
            image_path="skarlet.png",
            route="skarlet",
        )

        self.description = (
            (
                "Jeśli przy życiu pozostaje 5 lub więcej graczy, a Demon umrze, stajesz się Demonem. "
                "Skarlet staje się Demonem, gdy Demon umrze."
            ),
        )

    def game_over_conditions(self, game_state) -> bool:
        """Check game over conditions for the Skarlet character."""
        log_info("Checking game over conditions for Skarlet.")

        skarlet_player = next(
            (player for player in game_state.players if player.character == self), None
        )

        if skarlet_player is None:
            log_info("Skarlet is not in the game, skipping game over check.")
        elif not skarlet_player.is_alive():
            log_info("Skarlet is dead, skipping game over check.")
        else:
            is_any_demon_alive = any(
                player.is_alive()
                and player.character is not None
                and player.character.role_type == RoleType.DEMON
                for player in game_state.players
            )

            if is_any_demon_alive:
                log_info("A living Demon is still in play. Skarlet stays unchanged.")
                return []

            demon_player = next(
                (
                    player
                    for player in game_state.players
                    if player.character is not None
                    and player.character.role_type == RoleType.DEMON
                    and player.client_id != skarlet_player.client_id
                ),
                None,
            )

            if demon_player is None:
                log_info("No Demon player found to copy additional characters from.")
                return []

            skarlet_player.additional_characters = list(
                demon_player.additional_characters or []
            )
            demon_player.additional_characters = []
            tmp_skarlet = skarlet_player.character
            skarlet_player.character = demon_player.character
            demon_player.character = tmp_skarlet

            log_info(
                "Skarlet becomes the Demon and receives the Demon additional characters list."
            )

        return []
