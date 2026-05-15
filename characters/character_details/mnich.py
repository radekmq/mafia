from characters.character import Ability, Character, DualEffect, RenderPage, RoleType
from game_events import Event
from logger import log_info
from player import PlayerStatus

# = = = = = = = = = = = = =  RENDER PAGE = = = = = = = = = = = = =


def render_introduction(game_engine, current_player):
    """Render effect of the Mnich's ability during the introduction phase."""
    log_info("Get data for Mnich introduction.")
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
    """Render effect of the Mnich's ability during the night action phase."""
    log_info("Mnich's ability effect for night_minion_action called.")

    mnich_status = "Już wykonałeś swoją nocną akcję!"
    if current_player.is_night_action_done() or not current_player.is_alive():
        log_info("Current player has already completed their night action or is dead.")
        screen_content = "mnich_action_completed"
        mnich_status = "Wykonałeś już swoją nocną akcję lub ona tej nocy nie działa."
    elif game_engine.game_state.day == 0:
        log_info("This is the first night for the Mnich")
        screen_content = "confirm_first_night_action"
        mnich_status = "Pierwszej nocy Mnich nie wykonuje akcji, ponieważ demon nie może nikogo wyeliminować!"
    else:
        log_info("Rendering Mnich's night action page.")
        screen_content = "select_player"
        mnich_status = "Wybierz gracza, którego chcesz ochraniać przed Demonem."

    player_list = []
    if screen_content == "select_player":
        for player in game_engine.game_state.players:
            if player.client_id == current_player.client_id or player.character is None:
                continue
            if player.alive == PlayerStatus.DEAD:
                continue
            player_list.append(
                (
                    f"{player.name} (miejsce: {player.seat_no})",
                    player.client_id,
                )
            )
    log_info(f"Player list for Mnich's ability effect: {player_list}")
    player_character = current_player.character
    if current_player.drunk:
        player_character = current_player.additional_characters[0]

    return {
        "screen": "night_mnich",
        "character_data": {
            "role_name": player_character.name,
            "player_link": player_character.route,
            "player_image": player_character.image_path,
            "player_info": player_character.description,
            "screen_content": screen_content,
            "player_list": player_list,
            "mnich_status": mnich_status,
        },
    }


def render_night_resolution(game_engine, current_player):
    """Effect of the Mnich's ability during night_all_players_action state."""
    log_info("Get data for Mnich night resolution.")
    player_character = current_player.character
    if current_player.drunk:
        player_character = current_player.additional_characters[0]

    # Pobierz gracza chronionego przez Mnicha z game_state
    protected_player = game_engine.game_state.player_protected_by_mnich

    # Zresetuj ochronę Mnicha
    game_engine.game_state.reset_player_protected_by_mnich()

    return {
        "screen": "night_basic",
        "character_data": {
            "role_name": player_character.name,
            "player_link": player_character.route,
            "player_image": player_character.image_path,
            "player_info": player_character.description,
            "player_status": f"Gracz chroniony przez Mnicha: {protected_player.name if protected_player else 'Brak'}",
            "screen_content": "action_completed",
        },
    }


# = = = = = = = = = = = = =  ABILITY EFFECTS = = = = = = = = = = = = =


def ability_callback_mnich(data):
    """Handle callback for the Mnich's ability."""
    player, game_state, game_setup, callback_data = (
        data["actor"],
        data["game_state"],
        data["game_setup"],
        data["callback_data"],
    )
    log_info(f"Mnich's ability callback called with data: {callback_data}")
    selected_player_id = callback_data.get("selected_player")
    protected_player = game_state.get_player_by_client_id(selected_player_id)
    game_state.set_player_protected_by_mnich(protected_player)

    protected_character_power = 0.0
    if protected_player is not None and protected_player.character is not None:
        protected_character_power = game_setup.character_power.get(
            protected_player.character.name,
            0,
        )
    player.character.protected_character_power = float(protected_character_power)

    event = Event(
        name="confirm_night_action",
        actor_id=player.client_id,
        priority=50,
    )
    return [event]


def ability_night_resolution_original(data):
    """Handle callback for the Mnich's ability."""
    log_info(f"Mnich's ability callback called with data: {data}")
    game_state = data["game_state"]
    protected_by_mnich = game_state.get_player_protected_by_mnich()
    if protected_by_mnich is not None:
        log_info(f"Player protected by Mnich: {protected_by_mnich}")
        protected_by_mnich.set_protected(True)
    else:
        log_info("No player protected by Mnich.")


def ability_night_resolution_fake(data):
    log_info(f"Mnich's fake ability callback called with data: {data}")
    log_info("Nothing will happen if the player is drunk or poisoned.")


ability = Ability(
    night_resolution=DualEffect(
        original=ability_night_resolution_original,
        fake=ability_night_resolution_fake,
    ),
)
ability.callback_mnich = DualEffect(
    original=ability_callback_mnich,
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


class MnichCharacter(Character):
    """Class representing the Mnich character."""

    def __init__(self):
        """Initialize the Mnich character."""

        super().__init__(
            name="Mnich",
            role_type=RoleType.TOWNSFOLK,
            ability=ability,
            render_page=render_page,
            image_path="mnich.png",
            route="mnich",
        )

        self.description = (
            (
                "Każdej nocy wybierz gracza (nie siebie): tej nocy jest on bezpieczny przed Demonem."
                "Mnich chroni innych graczy przed Demonem."
            ),
        )
        self.protected_character_power = 0.0

    def evaluate_knowledge_score(self, _) -> float:
        """Evaluate knowledge score based on the information they have."""
        return self.protected_character_power / 5
