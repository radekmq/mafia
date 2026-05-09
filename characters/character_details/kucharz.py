import random

from characters.character import Ability, Character, DualEffect, RenderPage, RoleType
from logger import log_info
from player import PlayerStatus

# = = = = = = = = = = = = =  RENDER PAGE = = = = = = = = = = = = =


def render_introduction(game_engine, current_player):
    """Render effect of the Kucharz's ability during the introduction phase."""
    log_info("Get data for Kucharz introduction.")

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
    """Effect of the Kucharz's ability during night_all_players_action state."""
    log_info("Get data for Kucharz night action.")

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
    """Effect of the Kucharz's ability during night_all_players_action state."""
    log_info("Get data for Kucharz night resolution.")

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


def ability_setup_fake(data):
    """Fake setup for the Kucharz's ability, used for testing."""
    log_info("Kucharz is drunk, false information will be provided.")
    player, game_state, game_setup = (
        data["target"],
        data["game_state"],
        data["game_setup"],
    )

    evil_pairs = ability_setup_original(data)
    setup_for_player_count = next(
        (
            row
            for row in game_setup.trouble_brewing_setup
            if row.get("liczba_graczy") == len(game_state.players)
        ),
        None,
    )
    if setup_for_player_count is None:
        log_info("Brak konfiguracji Trouble Brewing dla liczby graczy, użyto 0.")
        max_evil_pairs = 0
    else:
        max_evil_pairs = setup_for_player_count.get("Minionki", 0)
    log_info(
        f"Maximum possible evil pairs based on minion characters: {max_evil_pairs}."
    )
    if max_evil_pairs == 0:
        log_info("No minion characters in setup, evil pairs will be set to 0.")
        evil_pairs_faked = 0
    else:
        evil_pairs_faked = random.randint(0, max_evil_pairs)
        if evil_pairs_faked == evil_pairs:
            log_info(
                "Random evil pairs match actual evil pairs, we try to randomize again."
            )
            evil_pairs_faked = random.randint(0, evil_pairs_faked)
    evil_pairs = evil_pairs_faked

    player.player_status = f"Kucharz wie, że liczba par złych graczy siedzących obok siebie to: {evil_pairs}"


def ability_setup_original(data):
    """Configure for the Kucharz's ability."""
    log_info("# # # # Setting up Kucharz's ability. # # # #")
    player, game_state, game_setup = (
        data["target"],
        data["game_state"],
        data["game_setup"],
    )

    players_in_seat_order = sorted(
        [candidate for candidate in game_state.players if candidate.character],
        key=lambda candidate: candidate.seat_no,
    )

    if len(players_in_seat_order) < 2:
        evil_pairs = 0
    else:
        evil_roles = {RoleType.MINION, RoleType.DEMON}
        evil_pairs = 0
        players_count = len(players_in_seat_order)

        for index, current_player in enumerate(players_in_seat_order):
            next_player = players_in_seat_order[(index + 1) % players_count]
            if (
                current_player.character.role_type in evil_roles
                and next_player.character.role_type in evil_roles
            ):
                evil_pairs += 1
    player.player_status = (
        f"Kucharz wie, że liczba par złych graczy siedzących obok siebie to: {evil_pairs}\n\n"
        f"Twoja wiedza nie może zostać zniekształcona przez otrucie."
    )
    return evil_pairs


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


class KucharzCharacter(Character):
    """Class representing the Kucharz character."""

    def __init__(self):
        """Initialize the Kucharz character."""

        super().__init__(
            name="Kucharz",
            role_type=RoleType.TOWNSFOLK,
            ability=ability,
            render_page=render_page,
            image_path="kucharz.png",
            route="kucharz",
        )

        self.description = (
            "Na początku wiesz, ile par złych graczy siedzi obok siebie. "
            "Kucharz wie, czy źli gracze siedzą obok siebie."
        )

    def evaluate_knowledge_score(self):
        """Evaluate knowledge score based on the information they have."""
        score = 2.0
        return score
