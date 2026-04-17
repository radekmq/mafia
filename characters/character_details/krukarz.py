from characters.character import Ability, Character, RoleType

def ability_effect_introduction(ct_game):
    current_player = ct_game.game_state.get_current_player()
    if not current_player:
        log_info("No current player found for Krukarz's ability introduction effect.")
        return render_inactive_page(ct_game)

    return render_player_page(ct_game, "player_page_night.html", {
        "role_name": current_player.character.name,
        "player_link": current_player.character.route,
        "player_image": current_player.character.image_path,
        "player_info": current_player.character.ability.description,
    })
    
    
def ability_effect_night_minion(ct_game):
    """Effect of the Krukarz's ability."""


def ability_callback(ct_game, data: dict):
    """Handle callback for the Krukarz's ability."""


def ability_setup(ct_game, player):
    """Configure for the Krukarz's ability."""


def on_night_exit(ct_game, player):
    """Handle actions to perform when the night phase ends for the Krukarz."""


char_ability = Ability(
    description=(
        "Jeśli umrzesz w nocy, zostajesz obudzony, aby wybrać gracza: poznajesz jego postać. "
        "Jeśli Krukarz umrze w nocy, może poznać postać jednego gracza."
    ),
    effect_introduction=ability_effect_introduction,
    effect_night_minion=ability_effect_night_minion,
    callback_night=ability_callback,
    setup=ability_setup,
    on_night_exit=on_night_exit,
)


class KrukarzCharacter(Character):
    """Class representing the Krukarz character."""

    def __init__(self):
        """Initialize the Krukarz character."""

        super().__init__(
            name="Krukarz",
            role_type=RoleType.TOWNSFOLK,
            ability=char_ability,
            image_path="krukarz.png",
            route="krukarz",
        )
