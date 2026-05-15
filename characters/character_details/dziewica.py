from characters.character import Ability, Character, DualEffect, RenderPage, RoleType
from logger import log_info
from player import PlayerStatus

# = = = = = = = = = = = = =  UTILITIES = = = = = = = = = = = = = =


# = = = = = = = = = = = = =  RENDER PAGE = = = = = = = = = = = = =


def render_introduction(game_engine, current_player):
    """Render effect of the Dziewica's ability during the introduction phase."""
    log_info("Get data for Dziewica introduction.")

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
    """Effect of the Dziewica's ability during night_all_players_action state."""
    log_info("Get data for Dziewica night action.")

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
    """Effect of the Dziewica's ability during night_all_players_action state."""
    log_info("Get data for Dziewica night resolution.")

    player_character = current_player.character
    if current_player.drunk:
        player_character = current_player.additional_characters[0]
    if (
        current_player.alive == PlayerStatus.DEAD
        and game_engine.game_state.nominated_by_imp_to_die is not current_player
    ):
        player_status = "Niestety Twoja zdolność już nie działa."
    else:
        player_status = "Twoja zdolność jest aktywna."

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


def ability_setup(data):
    """Configure for the Lokaj's ability."""
    log_info("Dziewica does not need setup.")
    player = data["target"]
    player.character.set_nominated(False)


ability = Ability(
    setup=DualEffect(
        original=ability_setup,
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


class DziewicaCharacter(Character):
    """Class representing the Dziewica character."""

    def __init__(self):
        """Initialize the Dziewica character."""

        super().__init__(
            name="Dziewica",
            role_type=RoleType.TOWNSFOLK,
            ability=ability,
            render_page=render_page,
            image_path="dziewica.png",
            route="dziewica",
        )

        self.description = (
            "Za pierwszym razem, gdy zostaniesz nominowany, jeśli nominujący jest Mieszczaninem, "
            "zostaje natychmiast stracony."
            "Dziewica może nieświadomie doprowadzić do egzekucji swojego oskarżyciela, "
            "jednocześnie potwierdzając, którzy gracze są Mieszczanami."
        )
        self.ever_nominated = False
        self.virgin_executed_player = False

    def evaluate_knowledge_score(self, _) -> float:
        """Evaluate knowledge score based on the information they have."""
        if self.virgin_executed_player:
            return 1.0
        return 0.0

    def on_virgin_nomination(self, nominee, nominator):
        """Handle the logic when the Dziewica is nominated for execution."""
        if nominee.drunk and nominee.poisoned:
            log_info(
                f"{nominee.name} was nominated for execution but Nominee is drunk or poisoned."
            )
        elif self.ever_nominated:
            log_info(
                f"{nominee.name} was nominated for execution but they were already nominated before."
            )
        elif nominator.character.role_type == RoleType.TOWNSFOLK:
            log_info(
                f"{nominee.name} was nominated for execution by {nominator.name} who is a Townsfolk."
            )
            self.virgin_executed_player = True

        self.ever_nominated = True
        return self.virgin_executed_player

    def set_nominated(self, nomination: bool):
        self.ever_nominated = nomination
