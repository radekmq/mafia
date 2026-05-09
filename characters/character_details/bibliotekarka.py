import random

from characters.character import Ability, Character, DualEffect, RenderPage, RoleType
from logger import log_info
from player import PlayerStatus

# = = = = = = = = = = = = =  RENDER PAGE = = = = = = = = = = = = =


def render_introduction(game_engine, current_player):
    """Render effect of the Bibliotekarka's ability during the introduction phase."""
    log_info("Get data for Bibliotekarka introduction.")

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
    """Effect of the Bibliotekarka's ability during night_all_players_action state."""
    log_info("Get data for Bibliotekarka night action.")

    screen_content = "confirm_night_action"
    player_status = "Potwierdź swoją nocną akcję."
    if (
        current_player.is_night_action_done()
        or current_player.alive == PlayerStatus.DEAD
    ):
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
    """Effect of the Bibliotekarka's ability during night_all_players_action state."""
    log_info("Get data for Bibliotekarka night resolution.")

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
    """Fake setup for the Bibliotekarka's ability, used when information is false."""
    log_info("Bibliotekarka is drunk, false information will be provided.")
    player, game_state, game_setup = (
        data["target"],
        data["game_state"],
        data["game_setup"],
    )
    players = game_state.players
    character_pool = game_setup.get_list_of_characters_by_type(RoleType.OUTSIDER)
    character_pool = [char.character for char in character_pool]

    if not character_pool:
        player.player_status = "W puli brak Outsiderów do wskazania."
        return

    outsider_character = random.choice(character_pool)
    eligible_players = [
        candidate for candidate in players if candidate.client_id != player.client_id
    ]

    shown_players = random.sample(eligible_players, min(2, len(eligible_players)))
    log_info(
        f"Number of shown players initially selected for Bibliotekarka's ability setup: {len(shown_players)}."
    )
    log_info(
        f"Bibliotekarka's ability setup: initially chosen players to show are {[p.name for p in shown_players]}."
    )
    matching_index = next(
        (
            i
            for i, c in enumerate(shown_players)
            if c.character and c.character.name == outsider_character.name
        ),
        None,
    )
    log_info(
        f"Bibliotekarka's ability setup: matching player index is {matching_index}."
    )

    if matching_index is not None and len(shown_players) == 2:
        log_info(
            f"Bibliotekarka's ability setup: found matching player {shown_players[matching_index].name} for the chosen outsider character."
        )
        other_player = shown_players[1 - matching_index]
        pool = [p for p in eligible_players if p.client_id != other_player.client_id]

        shown_players[matching_index] = random.choice(pool)
        log_info(
            f"Bibliotekarka's ability setup: replaced matching player with {shown_players[matching_index].name} from the pool."
        )

    shown_players_text = " lub ".join(
        f"{candidate.name} (miejsce: {candidate.seat_no})"
        for candidate in shown_players
    )

    if len(shown_players) < 2:
        player.player_status = (
            "Zbyt mało graczy aby zdolność Bibliotekarki mogła wskazać dwóch graczy."
        )
        return

    player.player_status = (
        f"Bibliotekarka wie, że jeden z graczy: {shown_players_text} "
        f"ma postać: {outsider_character.name}."
    )


def ability_setup_original(data):
    """Configure for the Bibliotekarka's ability."""
    log_info("# # # # Setting up Bibliotekarka's ability. # # # #")
    player, game_state = (data["target"], data["game_state"])
    players = game_state.players
    if player is None:
        return

    outsiders_in_play = [
        candidate
        for candidate in players
        if (
            candidate.character
            and candidate.character.role_type == RoleType.OUTSIDER
            and candidate.client_id != player.client_id
        )
    ]

    if not outsiders_in_play:
        player.player_status = "Bibliotekarka wie, że w grze nie ma Outsidera."
        return

    outsider_player = random.choice(outsiders_in_play)
    decoy_candidates = [
        candidate
        for candidate in players
        if candidate.client_id != outsider_player.client_id
        and candidate.client_id != player.client_id
    ]
    shown_players = [outsider_player]
    if decoy_candidates:
        shown_players.append(random.choice(decoy_candidates))
    else:
        player.player_status = "Bibliotekarka nie otrzymuje informacji o Outsiderze."
        return
    random.shuffle(shown_players)

    shown_players_text = "\n * " + "\n * ".join(
        f"{candidate.name} (miejsce: {candidate.seat_no})"
        for candidate in shown_players
    )
    player.player_status = (
        f"Bibliotekarka wie, że jeden z graczy ma postać {outsider_player.character.name}:\n"
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


class BibliotekarkaCharacter(Character):
    """Class representing the Bibliotekarka character."""

    def __init__(self):
        """Initialize the Bibliotekarka character."""

        super().__init__(
            name="Bibliotekarka",
            role_type=RoleType.TOWNSFOLK,
            ability=ability,
            render_page=render_page,
            image_path="bibliotekarka.png",
            route="bibliotekarka",
        )

        self.description = (
            "Na początku wiesz, że 1 z 2 graczy jest konkretnym Outsiderem "
            "(lub że żaden nie jest w grze). Bibliotekarka dowiaduje się, "
            "że konkretny Outsider jest w grze, ale nie kto go gra."
        )

    def evaluate_knowledge_score(self):
        """Evaluate knowledge score based on the information they have."""
        score = 2.0
        return score
