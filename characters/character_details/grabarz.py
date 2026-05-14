import random

from characters.character import Ability, Character, DualEffect, RenderPage, RoleType
from logger import log_info
from player import PlayerStatus

# = = = = = = = = = = = = =  UTILITIES = = = = = = = = = = = = =


# = = = = = = = = = = = = =  RENDER PAGE = = = = = = = = = = = = =


def render_introduction(game_engine, current_player):
    """Render effect of the Grabarz's ability during the introduction phase."""
    log_info("Get data for Grabarz introduction.")

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
    """Render Grabarz's night action confirmation."""
    log_info("Get data for Grabarz night action.")

    screen_content = "confirm_night_action"
    player_status = "Potwierdź swoją nocną akcję."
    if (
        current_player.is_night_action_done()
        or current_player.alive == PlayerStatus.DEAD
    ):
        log_info("Current player has already completed their night action or is dead.")
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
    """Render Grabarz's information after night resolution."""
    log_info("Get data for Grabarz night resolution.")

    player_character = current_player.character
    if current_player.drunk:
        player_character = current_player.additional_characters[0]
    if (
        current_player.alive == PlayerStatus.DEAD
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


def ability_night_resolution_original(data):
    """Resolve Grabarz's true night information."""
    log_info("# # # # Resolving Grabarz's ability. # # # #")
    player, game_state, _game_setup = (
        data["target"],
        data["game_state"],
        data["game_setup"],
    )

    executed_player = game_state.last_executed_player
    if executed_player is None or executed_player.character is None:
        player.player_status = "Poprzedniego dnia miasto nikogo nie wyeliminowało."
        return None

    executed_character_name = executed_player.character.name
    recluse_heuristic = getattr(executed_player.character, "recluse_heuristic", None)
    if recluse_heuristic is not None:
        executed_character_name = recluse_heuristic.grabarz_asks_for_character(
            executed_player
        )

    player.player_status = (
        "Grabarz wie, że postać wyeliminowana przez miasto poprzedniego dnia to: "
        f"{executed_character_name}."
    )

    if executed_character_name == executed_player.character.name:
        player.character.correctly_identified_characters += 1
    else:
        player.character.incorrectly_identified_characters += 1

    return executed_character_name


def ability_night_resolution_fake(data):
    """Resolve Grabarz's false night information."""
    log_info("Grabarz is drunk or poisoned, false information will be provided.")
    player, game_state, _game_setup = (
        data["target"],
        data["game_state"],
        data["game_setup"],
    )

    executed_player = game_state.last_executed_player
    if executed_player is None or executed_player.character is None:
        player.player_status = "Poprzedniego dnia miasto nikogo nie wyeliminowało."
        return None

    all_characters = _game_setup.get_dict_of_characters()
    available_characters = [
        character
        for characters in all_characters.values()
        for character in characters
        if character.name != "Grabarz"
    ]

    if not available_characters:
        player.player_status = "Brak dostępnych postaci do pokazania Grabarzowi."
        return None

    shown_character = random.choice(available_characters)
    player.player_status = (
        "Grabarz wie, że postać wyeliminowana przez miasto poprzedniego dnia to: "
        f"{shown_character.name}."
    )
    player.character.incorrectly_identified_characters += 1
    return shown_character.name


ability = Ability(
    night_resolution=DualEffect(
        original=ability_night_resolution_original,
        fake=ability_night_resolution_fake,
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


class GrabarzCharacter(Character):
    """Class representing the Grabarz character."""

    def __init__(self):
        """Initialize the Grabarz character."""

        super().__init__(
            name="Grabarz",
            role_type=RoleType.TOWNSFOLK,
            ability=ability,
            render_page=render_page,
            image_path="grabarz.png",
            route="grabarz",
        )

        self.description = (
            "Każdej nocy dowiadujesz się, jaka postać została dziś stracona."
            "Grabarz dowiaduje się kogo stracono w ciągu dnia."
        )
        self.correctly_identified_characters = 0
        self.incorrectly_identified_characters = 0

    def evaluate_knowledge_score(self, _) -> float:
        """Evaluate knowledge score based on the information they have."""
        return (self.correctly_identified_characters * 3) + (
            self.incorrectly_identified_characters * -2
        )
