import random

from characters.character import Ability, Character, DualEffect, RenderPage, RoleType
from logger import log_info
from player import PlayerStatus

# = = = = = = = = = = = = =  UTILITIES = = = = = = = = = = = = =


def is_recluse_player(player):
    """Check whether a player is the Recluse/Pustelnik."""
    return player is not None and player.character.name == "Pustelnik"


def get_recluse_registration_for_empata(player):
    """Return how the Recluse registers for Empata."""
    recluse_heuristic = getattr(player.character, "recluse_heuristic", None)
    if recluse_heuristic is None:
        return None

    return recluse_heuristic.empata_asks_for_neighbors(player)


def get_character_names_by_type(game_setup, character_type):
    """Get all character names for a role type from the scenario setup."""
    characters_by_type = game_setup.get_dict_of_characters()
    return {character.name for character in characters_by_type.get(character_type, [])}


def is_registered_as_minion(registered_role, game_setup):
    """Check whether the Recluse registered as a minion."""
    return registered_role in get_character_names_by_type(game_setup, "minion")


def is_registered_as_demon(registered_role, game_setup):
    """Check whether the Recluse registered as a demon."""
    return registered_role in get_character_names_by_type(game_setup, "demon")


def count_evil_alive_neighbors(player, game_state, game_setup):
    """Count evil characters among Empata's closest alive neighbors."""
    alive_neighbors = get_alive_neighbors(player, game_state)

    evil_roles = {RoleType.MINION, RoleType.DEMON}
    evil_neighbors_count = 0
    recluse_registered_as_minion = False
    actual_minion_neighbor_found = False

    for neighbor in alive_neighbors:
        if not neighbor or not neighbor.character:
            continue

        if neighbor.character.role_type in evil_roles:
            evil_neighbors_count += 1
            if neighbor.character.role_type == RoleType.MINION:
                actual_minion_neighbor_found = True
            continue

        if not is_recluse_player(neighbor):
            continue

        registered_role = get_recluse_registration_for_empata(neighbor)
        if is_registered_as_minion(registered_role, game_setup):
            recluse_registered_as_minion = True
            evil_neighbors_count += 1
            continue

        if is_registered_as_demon(registered_role, game_setup):
            evil_neighbors_count += 1

    alive_neighbors_count = len([neighbor for neighbor in alive_neighbors if neighbor])
    if (
        alive_neighbors_count == 2
        and recluse_registered_as_minion
        and actual_minion_neighbor_found
        and evil_neighbors_count > 1
    ):
        return 1

    return evil_neighbors_count


def get_alive_neighbors(player, game_state):
    """Get Empata's closest alive neighbors on both sides."""
    players_in_seat_order = sorted(
        [candidate for candidate in game_state.players if candidate.character],
        key=lambda candidate: candidate.seat_no,
    )

    if player not in players_in_seat_order or len(players_in_seat_order) < 2:
        return (None, None)

    current_index = players_in_seat_order.index(player)
    players_count = len(players_in_seat_order)

    def find_alive_neighbor(step):
        for offset in range(1, players_count):
            candidate = players_in_seat_order[
                (current_index + step * offset) % players_count
            ]
            if candidate.alive == PlayerStatus.ALIVE:
                return candidate
        return None

    return (find_alive_neighbor(-1), find_alive_neighbor(1))


def get_alive_neighbors_cache_key(player, game_state):
    """Build a stable cache key from Empata's current alive neighbors."""
    return tuple(
        neighbor.client_id if neighbor else None
        for neighbor in get_alive_neighbors(player, game_state)
    )


def set_player_status(player, evil_neighbors_count):
    """Set Empata's information text."""
    player.player_status = (
        "Empata wie, że liczba złych postaci (Minion lub Demon) "
        f"wśród jego żywych sąsiadów wynosi: {evil_neighbors_count}"
    )


# = = = = = = = = = = = = =  RENDER PAGE = = = = = = = = = = = = =


def render_introduction(game_engine, current_player):
    """Render effect of the Empata's ability during the introduction phase."""
    log_info("Get data for Empata introduction.")

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
    """Render Empata's night action confirmation."""
    log_info("Get data for Empata night action.")

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
    """Render Empata's information after night resolution."""
    log_info("Get data for Empata night resolution.")

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
    """Resolve Empata's true night information."""
    log_info("# # # # Resolving Empata's ability. # # # #")
    player, game_state, _game_setup = (
        data["target"],
        data["game_state"],
        data["game_setup"],
    )

    evil_neighbors_count = count_evil_alive_neighbors(player, game_state, _game_setup)
    if evil_neighbors_count == 2:
        player.character.detected_double_evil_zone = 1
    if evil_neighbors_count == 1:
        player.character.consistent_readings = 1
    set_player_status(player, evil_neighbors_count)
    return evil_neighbors_count


def ability_night_resolution_fake(data):
    """Resolve Empata's false night information."""
    log_info("Empata is drunk or poisoned, false information will be provided.")
    player, game_state, _game_setup = (
        data["target"],
        data["game_state"],
        data["game_setup"],
    )

    evil_neighbors_count = count_evil_alive_neighbors(player, game_state, _game_setup)
    false_counts = [count for count in range(3) if count != evil_neighbors_count]

    cache_key = get_alive_neighbors_cache_key(player, game_state)
    fake_results_cache = getattr(player, "empata_fake_results", {})

    if cache_key not in fake_results_cache:
        fake_results_cache[cache_key] = random.choice(false_counts)
        player.empata_fake_results = fake_results_cache

    evil_neighbors_count = fake_results_cache[cache_key]

    set_player_status(player, evil_neighbors_count)
    player.character.consistent_readings = 0
    player.character.detected_double_evil_zone = 0
    return evil_neighbors_count


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


class EmpataCharacter(Character):
    """Class representing the Empata character."""

    def __init__(self):
        """Initialize the Empata character."""

        super().__init__(
            name="Empata",
            role_type=RoleType.TOWNSFOLK,
            ability=ability,
            render_page=render_page,
            image_path="empata.png",
            route="empata",
        )

        self.description = (
            "Po każdej nocy Empata dowiaduje się, ilu z jego dwóch "
            "żyjących sąsiadów jest złych. Empata uczy się, "
            "czy sąsiadujący z nim gracze są dobrzy czy źli."
        )
        self.consistent_readings = 0.5
        self.detected_double_evil_zone = 0

    def evaluate_knowledge_score(self, _) -> float:
        """Evaluate knowledge score based on the information they have."""
        score = 0.0
        score += self.consistent_readings * 2.0

        if self.detected_double_evil_zone:
            score += 5.0

        return score
