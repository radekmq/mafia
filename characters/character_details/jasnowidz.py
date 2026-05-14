import random

from characters.character import Ability, Character, DualEffect, RenderPage, RoleType
from game_events import Event
from logger import log_info
from player import PlayerStatus

# = = = = = = = = = = = = =  UTILITIES = = = = = = = = = = = = = =


def is_recluse_player(target_player):
    """Check whether the selected player is the Recluse/Pustelnik."""
    return target_player is not None and target_player.character.name == "Pustelnik"


def is_demon_player(target_player):
    """Check whether the selected player is an actual demon."""
    return (
        target_player is not None
        and target_player.character.role_type == RoleType.DEMON
    )


def get_cached_recluse_imp_registration(player, target_player):
    """Return whether this Jasnowidz already learned that given Recluse registers as Imp."""
    recluse_registrations = getattr(player.character, "recluse_registered_as_imp", {})
    return recluse_registrations.get(target_player.client_id, False)


def cache_recluse_imp_registration(player, target_player):
    """Persist that this Recluse registers as Imp for this Jasnowidz."""
    recluse_registrations = getattr(player.character, "recluse_registered_as_imp", {})
    recluse_registrations[target_player.client_id] = True
    player.character.recluse_registered_as_imp = recluse_registrations


def should_recluse_register_as_imp_for_jasnowidz(player, selected_targets):
    """Check whether Jasnowidz may get a false Demon result because of Recluse."""
    recluse_targets = [
        target for target in selected_targets if is_recluse_player(target)
    ]
    if not recluse_targets:
        return None

    for recluse_target in recluse_targets:
        if get_cached_recluse_imp_registration(player, recluse_target):
            log_info(
                f"Jasnowidz uses cached Recluse->Imp registration for player: {recluse_target.name}"
            )
            return recluse_target

    if len(selected_targets) != 2:
        return None

    for recluse_target in recluse_targets:
        other_target = next(
            (
                target
                for target in selected_targets
                if target.client_id != recluse_target.client_id
            ),
            None,
        )
        if other_target is None or is_demon_player(other_target):
            continue

        recluse_heuristic = getattr(recluse_target.character, "recluse_heuristic", None)
        if recluse_heuristic is None:
            continue

        if recluse_heuristic.should_recluse_fake("Jasnowidz"):
            cache_recluse_imp_registration(player, recluse_target)
            log_info(f"Recluse registered as Imp for Jasnowidz: {recluse_target.name}")
            return recluse_target

    return None


def ability_callback_i_see_you(data):
    """Handle callback for the Jasnowidz's ability."""
    player, game_state, game_setup, callback_data = (
        data["target"],
        data["game_state"],
        data["game_setup"],
        data["callback_data"],
    )
    log_info(f"Jasnowidz's ability callback called with data: {callback_data}")
    player.character.selected_players_to_see = callback_data.get("selected_players")

    event = Event(
        name="confirm_night_action",
        actor_id=player.client_id,
        priority=50,
    )
    return [event]


# = = = = = = = = = = = = =  RENDER PAGE = = = = = = = = = = = = =


def render_introduction(game_engine, current_player):
    """Render effect of the Jasnowidzs's ability during the introduction phase."""
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
    """Render effect of the Jasnowidz's ability during the night action phase."""
    log_info("Jasnowidz's ability effect for night_minion_action called.")
    player_character = current_player.character

    jasnowidz_status = "Już wykonałeś swoją nocną akcję!"
    if (
        current_player.is_night_action_done()
        or current_player.alive == PlayerStatus.DEAD
    ):
        log_info("Current player has already completed their night action or is dead.")
        screen_content = "jasnowidz_action_completed"
        jasnowidz_status = "Potwierdziłeś swoją nocną akcję lub ona nie działa."
    else:
        log_info("Rendering Jasnowidz's night action page.")
        screen_content = "select_player_to_see"
        jasnowidz_status = "Wybierz gracza, którego rolę chcesz poznać."

    player_list = []
    if screen_content == "select_player_to_see":
        for player in game_engine.game_state.players:
            player_list.append(
                (
                    f"{player.name} (miejsce: {player.seat_no})",
                    player.client_id,
                )
            )
    log_info(f"Player list for Jasnowidz's ability effect: {player_list}")

    return {
        "screen": "night_jasnowidz",
        "character_data": {
            "role_name": player_character.name,
            "player_link": player_character.route,
            "player_image": player_character.image_path,
            "player_info": player_character.description,
            "screen_content": screen_content,
            "player_list": player_list,
            "jasnowidz_status": jasnowidz_status,
        },
    }


def render_night_resolution(game_engine, current_player):
    """Effect of the Jasnowidz's ability during night_all_players_action state."""
    log_info(f"Jasnowidz's ability: {current_player.player_status}.")
    player_character = current_player.character

    if (
        current_player.alive == PlayerStatus.DEAD
        and game_engine.game_state.nominated_by_imp_to_die is not current_player
    ):
        player_status = "Niestety Twoja zdolność już nie działa."
    else:
        player_status = (
            current_player.jasnowidz_status
            if hasattr(current_player, "jasnowidz_status")
            else "Brak informacji o wyniku zdolności jasnowidza."
        )

    return {
        "screen": "night_jasnowidz",
        "character_data": {
            "role_name": player_character.name,
            "player_link": player_character.route,
            "player_image": player_character.image_path,
            "player_info": player_character.description,
            "screen_content": "jasnowidz_action_completed",
            "player_list": [],
            "jasnowidz_status": player_status,
        },
    }


# = = = = = = = = = = = = =  ABILITY EFFECTS = = = = = = = = = = = = =


def ability_setup(data):
    """Configure for the Jasnowidz's ability."""
    log_info("Jasnowidz does not need setup.")
    player, game_state, game_setup = (
        data["target"],
        data["game_state"],
        data["game_setup"],
    )
    if not hasattr(player.character, "cached_fake_night_result"):
        player.character.cached_fake_night_result = {}
    if not hasattr(player.character, "recluse_registered_as_imp"):
        player.character.recluse_registered_as_imp = {}


def ability_night_resolution_original(data):
    """Handle callback for the Jasnowidz's ability."""
    log_info(f"Jasnowidz's ability callback called with data: {data}")
    player, game_state, game_setup = (
        data["target"],
        data["game_state"],
        data["game_setup"],
    )

    if (
        hasattr(player.character, "selected_players_to_see")
        and player.character.selected_players_to_see
    ):
        selected_players = player.character.selected_players_to_see
        log_info(f"Jasnowidz selected players to see: {selected_players}")
        selected_targets = [
            game_state.get_player_by_client_id(selected_player_id)
            for selected_player_id in selected_players
        ]

        is_deamon_found = False
        for target_player in selected_targets:
            if is_demon_player(target_player):
                player.jasnowidz_status = "Wiesz, że wśród wskazanych przez Ciebie wybranych graczy jest Demon."
                is_deamon_found = True
                break

        if not is_deamon_found:
            recluse_registered_as_imp = should_recluse_register_as_imp_for_jasnowidz(
                player, selected_targets
            )
            if recluse_registered_as_imp is not None:
                player.jasnowidz_status = (
                    "Wiesz, że wśród wskazanych przez Ciebie graczy jest Demon."
                )
                is_deamon_found = True

        if is_deamon_found:
            player.jasnowidz_status = (
                "Wiesz, że wśród wskazanych przez Ciebie graczy jest Demon."
            )
            player.character.useful_yes_results += 1
        else:
            player.jasnowidz_status = (
                "Nie ma Demona wśród wskazanych przez Ciebie graczy."
            )
            player.character.confirmed_no_results += 1
    else:
        player.jasnowidz_status = "Żadna informacja nie jest dostępna dla jasnowidza."

    player.character.selected_players_to_see = None
    return []


def ability_night_resolution_fake(data):
    log_info(f"Jasnowidz's fake ability callback called with data: {data}")
    player, game_state, game_setup = (
        data["target"],
        data["game_state"],
        data["game_setup"],
    )

    if (
        hasattr(player.character, "selected_players_to_see")
        and player.character.selected_players_to_see
    ):
        selected_players = player.character.selected_players_to_see
        log_info(f"Jasnowidz selected players to see: {selected_players}")

        selected_targets = [
            game_state.get_player_by_client_id(selected_player_id)
            for selected_player_id in selected_players
        ]

        is_deamon_found = False
        for target_player in selected_targets:
            if is_demon_player(target_player):
                player.jasnowidz_status = "Wiesz, że wśród wskazanych przez Ciebie wybranych graczy jest Demon."
                is_deamon_found = True
                break

        random_result = player.character.cached_fake_night_result.get(
            frozenset(selected_players)
        )
        if random_result is not None:
            log_info(
                f"Using cached fake night result for selected players: {random_result}"
            )
        else:
            # If demon was found, we want to ensure that the fake result is supporting evil
            if is_deamon_found:
                random_result = False
            else:
                random_result = random.choice([True, False])
            player.character.cached_fake_night_result[
                frozenset(selected_players)
            ] = random_result

        if random_result:
            player.jasnowidz_status = (
                "Wiesz, że wśród wskazanych przez Ciebie graczy jest Demon."
            )
        else:
            player.jasnowidz_status = (
                "Nie ma Demona wśród wskazanych przez Ciebie graczy."
            )
    else:
        player.jasnowidz_status = "Żadna informacja nie jest dostępna dla jasnowidza."

    player.character.selected_players_to_see = None
    return []


ability = Ability(
    setup=DualEffect(
        original=ability_setup,
    ),
    night_resolution=DualEffect(
        original=ability_night_resolution_original,
        fake=ability_night_resolution_fake,
    ),
)
ability.callback_i_see_you = DualEffect(
    original=ability_callback_i_see_you,
)


render_page = RenderPage(
    introduction=DualEffect(
        original=render_introduction,
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


class JasnowidzCharacter(Character):
    """Class representing the Jasnowidz character."""

    def __init__(self):
        """Initialize the Jasnowidz character."""

        super().__init__(
            name="Jasnowidz",
            role_type=RoleType.TOWNSFOLK,
            ability=ability,
            render_page=render_page,
            image_path="jasnowidz.png",
            route="jasnowidz",
        )

        self.description = (
            (
                "Po każdej nocy wybierz 2 graczy: dowiadujesz się, "
                "czy którykolwiek z nich jest Demonem. Jasnowidz dowiaduje się, "
                "czy którykolwiek z dwóch graczy jest Demonem."
            ),
        )
        self.useful_yes_results = 0
        self.confirmed_no_results = 0

    def evaluate_knowledge_score(self, _) -> float:
        """Evaluate knowledge score based on the information they have."""
        score = 0.0
        # liczba trafień zawężających demona
        score += self.useful_yes_results * 2.0
        # liczba potwierdzonych NO
        score += self.confirmed_no_results * 1.0

        return score
