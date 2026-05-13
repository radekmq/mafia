import random

from characters.character import Ability, Character, DualEffect, RenderPage, RoleType
from logger import log_info
from player import PlayerStatus

# = = = = = = = = = = = = =  RENDER PAGE = = = = = = = = = = = = =


def render_introduction(game_engine, current_player):
    """Render effect of the Detektyw's ability during the introduction phase."""
    log_info("Get data for Detektyw introduction.")

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
    """Effect of the Detektyw's ability during night_all_players_action state."""
    log_info("Get data for Detektyw night action.")

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
    """Effect of the Detektyw's ability during night_all_players_action state."""
    log_info("Get data for Detektyw night resolution.")

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


def format_shown_players(shown_players):
    """Format shown players as a multiline list."""
    return "\n * " + "\n * ".join(
        f"{candidate.name} (miejsce: {candidate.seat_no})"
        for candidate in shown_players
    )


def get_recluse_registration_for_detektyw(players):
    """Return the Recluse player and how they register for Detektyw."""
    recluse_player = next(
        (
            candidate
            for candidate in players
            if candidate.character and candidate.character.name == "Pustelnik"
        ),
        None,
    )
    if recluse_player is None:
        return None, None

    recluse_heuristic = getattr(recluse_player.character, "heuristic", None)
    if recluse_heuristic is None:
        return recluse_player, None

    return recluse_player, recluse_heuristic.detektyw_asks_for_demon(recluse_player)


def is_registered_as_minion(game_setup, character_name):
    """Check whether the registered character is a minion from the scenario."""
    minion_names = {
        character.name
        for character in game_setup.get_dict_of_characters().get("minion", [])
    }
    return character_name in minion_names


def ability_setup_fake(data):
    """Fake setup for the Detektyw's ability, used when information is false."""
    log_info("Detektyw is drunk, false information will be provided.")
    player, game_state, game_setup = (
        data["target"],
        data["game_state"],
        data["game_setup"],
    )
    player.character.used_fake_setup = True
    players = game_state.players
    character_pool = game_setup.get_list_of_characters_by_type(RoleType.MINION)
    character_pool = [char.character for char in character_pool]

    if not character_pool:
        player.player_status = "W puli brak Minionów do wskazania."
        return

    minion_character = random.choice(character_pool)
    eligible_players = [
        candidate for candidate in players if candidate.client_id != player.client_id
    ]

    shown_players = random.sample(eligible_players, min(2, len(eligible_players)))
    log_info(
        f"Number of shown players initially selected for Detektyw's ability setup: {len(shown_players)}."
    )
    log_info(
        f"Detektyw's ability setup: initially chosen players to show are {[p.name for p in shown_players]}."
    )
    matching_index = next(
        (
            i
            for i, c in enumerate(shown_players)
            if c.character and c.character.name == minion_character.name
        ),
        None,
    )
    log_info(f"Detektyw's ability setup: matching player index is {matching_index}.")

    if matching_index is not None and len(shown_players) == 2:
        log_info(
            f"Detektyw's ability setup: found matching player {shown_players[matching_index].name} for the chosen minion character."
        )
        other_player = shown_players[1 - matching_index]
        pool = [p for p in eligible_players if p.client_id != other_player.client_id]

        shown_players[matching_index] = random.choice(pool)
        log_info(
            f"Detektyw's ability setup: replaced matching player with {shown_players[matching_index].name} from the pool."
        )

    if len(shown_players) < 2:
        player.player_status = (
            "Zbyt mało graczy aby zdolność Detektywa mogła wskazać dwóch graczy."
        )
        return

    shown_players_text = format_shown_players(shown_players)
    player.player_status = (
        f"Detektyw wie, że jeden z graczy: {shown_players_text} \n"
        f"ma postać: {minion_character.name}."
    )


def ability_setup_original(data):
    """Configure for the Detektyw's ability."""
    log_info("# # # # Setting up Detektyw's ability. # # # #")
    player, game_state, game_setup = (
        data["target"],
        data["game_state"],
        data["game_setup"],
    )
    players = game_state.players
    if player is None:
        return
    player.character.used_fake_setup = False

    (
        recluse_player,
        recluse_registered_character,
    ) = get_recluse_registration_for_detektyw(players)

    minions_in_play = [
        candidate
        for candidate in players
        if (
            candidate.character
            and candidate.character.role_type == RoleType.MINION
            and candidate.client_id != player.client_id
        )
    ]

    if not minions_in_play:
        player.player_status = "Detektyw nie otrzymuje informacji o Minionie."
        return

    minion_candidates = list(minions_in_play)
    if (
        recluse_player is not None
        and recluse_player.client_id != player.client_id
        and is_registered_as_minion(game_setup, recluse_registered_character)
    ):
        minion_candidates.append(recluse_player)

    shown_minion_player = random.choice(minion_candidates)
    shown_as_minion_name = shown_minion_player.character.name
    if shown_minion_player == recluse_player:
        shown_as_minion_name = recluse_registered_character

    decoy_candidates = [
        candidate
        for candidate in players
        if candidate.client_id != shown_minion_player.client_id
        and candidate.client_id != player.client_id
    ]

    if shown_minion_player == recluse_player:
        decoy_candidates = [
            candidate
            for candidate in decoy_candidates
            if candidate.character is not None
            and candidate.character.name != shown_as_minion_name
        ]

    shown_players = [shown_minion_player]
    if decoy_candidates:
        shown_players.append(random.choice(decoy_candidates))
    else:
        player.player_status = "Detektyw nie otrzymuje informacji o Minionie."
        return
    random.shuffle(shown_players)

    shown_players_text = format_shown_players(shown_players)
    player.player_status = (
        f"Detektyw wie, że jeden z graczy ma postać {shown_as_minion_name}:\n"
        f"{shown_players_text} \n\n"
        f"Twoja wiedza nie może zostać zniekształcona przez otrucie."
    )


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


class DetektywCharacter(Character):
    """Class representing the Detektyw character."""

    def __init__(self):
        """Initialize the Detektyw character."""

        super().__init__(
            name="Detektyw",
            role_type=RoleType.TOWNSFOLK,
            ability=ability,
            render_page=render_page,
            image_path="detektyw.png",
            route="detektyw",
        )

        self.description = (
            "Na początku wiesz, że 1 z 2 graczy jest konkretnym Minionem. "
            "Detektyw dowiaduje się, że konkretny Minion jest w grze, "
            "ale nie kto go gra."
        )
        self.used_fake_setup = False

    def evaluate_knowledge_score(self, _) -> float:
        """Evaluate knowledge score based on the information they have."""
        if self.used_fake_setup:
            return -1.0
        return 2.0
