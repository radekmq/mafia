import random

from characters.character import Ability, Character, DualEffect, RenderPage, RoleType
from logger import log_info

# = = = = = = = = = = = = =  UTILITIES = = = = = = = = = = = = = =


# = = = = = = = = = = = = =  RENDER PAGE = = = = = = = = = = = = =


def render_introduction(game_engine, current_player):
    """Render effect of the Baron's ability during the introduction phase."""
    log_info("Get data for Baron introduction.")

    player_character = current_player.character
    if current_player.drunk:
        player_character = current_player.additional_characters[0]

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
    """Effect of the Baron's ability during night_all_players_action state."""
    log_info("Get data for Baron night action.")

    screen_content = "confirm_night_action"
    player_status = "Potwierdź swoją nocną akcję."
    if current_player.is_night_action_done() or not current_player.is_alive():
        log_info("Current player has already completed their night action.")
        screen_content = "action_completed"
        player_status = "Potwierdziłeś swoją nocną akcję lub ona nie działa."

    player_character = current_player.character
    if current_player.drunk:
        player_character = current_player.additional_characters[0]

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
    """Effect of the Baron's ability during night_all_players_action state."""
    log_info("Get data for Baron night resolution.")

    player_character = current_player.character
    if current_player.drunk:
        player_character = current_player.additional_characters[0]
    if (
        not current_player.is_alive()
        and game_engine.game_state.nominated_by_imp_to_die is not current_player
    ):
        player_status = "Niestety Twoja zdolność już nie działa."
    else:
        player_status = current_player.player_status

    return {
        "screen": "night_basic",
        "character_data": {
            "role_name": player_character.name,
            "player_link": player_character.route,
            "player_image": player_character.image_path,
            "player_info": player_character.description,
            "player_status": player_status,
            "screen_content": "action_completed",
        },
    }


# = = = = = = = = = = = = =  ABILITY EFFECTS = = = = = = = = = = = = =


def ability_setup_fake(data):
    """Fake setup for the Baron's ability, used when information is false."""
    # It's actually not possible that Baron is drunk.
    # It does not matter if it's poisoned or not, because the ability is not working when he's drunk.


def ability_setup_original(data):
    """Configure for the Baron's ability."""
    log_info("# # # # Setting up Baron's ability. # # # #")
    player, game_state, game_setup = (
        data["target"],
        data["game_state"],
        data["game_setup"],
    )
    player.character.used_fake_setup = False
    players = game_state.players
    if player is None:
        return

    townsfolk_characters = [
        player for player in players if player.character.role_type == RoleType.TOWNSFOLK
    ]

    # Randomly select 2 players from the list of townsfolk characters
    if len(townsfolk_characters) < 2:
        player.player_status = (
            "Zbyt mało graczy aby zdolność Bibliotekarki mogła wskazać dwóch graczy."
        )
        return
    chosen_players = random.sample(townsfolk_characters, 2)

    # Randomly assign new outsider character to one of the chosen players
    available_outsiders = [
        char.character
        for char in game_setup.get_list_of_characters_by_type(RoleType.OUTSIDER)
    ]

    # Randomly select 2 outsider characters from the available pool, should not repeat the same character
    if len(available_outsiders) < 2:
        player.player_status = "Zbyt mało Outsiderów w puli, aby przypisać do graczy."
        return
    selected_outsiders = random.sample(available_outsiders, 2)

    # Assign the selected outsider characters to the chosen players
    for i, chosen_player in enumerate(chosen_players):
        chosen_player.character = selected_outsiders[i]

    player.player_status = "Wiesz, że w grze jest dodatkowych dwóch Outsiderów."


ability = Ability(
    setup=DualEffect(
        original=ability_setup_original,
        fake=ability_setup_fake,
    )
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


class BaronCharacter(Character):
    """Class representing the Baron character."""

    def __init__(self):
        """Initialize the Baron character."""

        super().__init__(
            name="Baron",
            role_type=RoleType.MINION,
            ability=ability,
            render_page=render_page,
            image_path="baron.png",
            route="baron",
        )

        self.description = (
            (
                "W grze jest dodatkowa liczba Outsiderów. [+2 Outsiderów] "
                "Baron zmienia liczbę Outsiderów obecnych w grze."
            ),
        )
        self.used_fake_setup = False

    def evaluate_knowledge_score(self, _) -> float:
        """Evaluate knowledge score based on the information they have."""
        if self.used_fake_setup:
            return -1.0
        return 2.0
