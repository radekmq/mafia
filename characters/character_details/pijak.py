import random

from characters.character import Ability, Character, DualEffect, RenderPage, RoleType
from logger import log_info

# = = = = = = = = = = = = =  RENDER PAGE = = = = = = = = = = = = =


def render_introduction(game_engine, current_player):
    """Render effect of the Pijak's ability during the introduction phase."""
    log_info("Get data for Pijak introduction.")
    drunk_character = current_player.additional_characters[0]
    return drunk_character.render_page.introduction(
        game_engine, current_player, is_fake=True
    )


def render_night_action(game_engine, current_player):
    """Render effect of the Pijak's ability during the night action phase."""
    log_info("Get data for Pijak night action.")
    drunk_character = current_player.additional_characters[0]
    return drunk_character.render_page.night_action(
        game_engine, current_player, is_fake=True
    )


def render_night_resolution(game_engine, current_player):
    """Render effect of the Pijak's ability during the night resolution phase."""
    log_info("Get data for Pijak night resolution.")
    drunk_character = current_player.additional_characters[0]
    return drunk_character.render_page.night_resolution(
        game_engine, current_player, is_fake=True
    )


# = = = = = = = = = = = = =  ABILITY EFFECTS = = = = = = = = = = = = =


def ability_setup(data):
    """Configure for the Pijak's ability."""
    player = data["target"]
    game_setup = data["game_setup"]
    list_of_available_good_chars = game_setup.get_list_of_characters_by_type(
        RoleType.TOWNSFOLK, available_only=True
    )
    if len(list_of_available_good_chars) < 1:
        raise ValueError(
            "Not enough Townsfolk characters available for Pijak's ability setup."
        )
    random_townsfolk = random.sample(list_of_available_good_chars, 1)
    random_character = random_townsfolk[0].character
    player.additional_characters = [random_character]
    random_townsfolk[0].assigned_in_play += 1
    log_info(
        f"Pijak's ability setup: assigned additional characters to Pijak: {random_character.name}"
    )
    player.drunk = True
    return random_character.ability.setup(data, is_fake=True)


def ability_night_action(data):
    """Effect of the Pijak's ability."""
    log_info(
        "Pijak's night action called, forwarding to additional character's ability effect."
    )
    current_player = data["target"]
    return current_player.additional_characters[0].ability.night_action(
        data, is_fake=True
    )


def ability_night_resolution(data):
    """Effect of the Pijak's ability during the night resolution phase."""
    log_info(
        "Pijak's night resolution called, forwarding to additional character's ability effect."
    )
    current_player = data["target"]
    return current_player.additional_characters[0].ability.night_resolution(
        data, is_fake=True
    )


ability = Ability(
    setup=DualEffect(
        original=ability_setup,
    ),
    night_action=DualEffect(
        original=ability_night_action,
        fake=ability_night_action,
    ),
    night_resolution=DualEffect(
        original=ability_night_resolution,
        fake=ability_night_resolution,
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


class PijakCharacter(Character):
    """Class representing the Pijak character."""

    def __init__(self):
        """Initialize the Pijak character."""

        super().__init__(
            name="Pijak",
            role_type=RoleType.OUTSIDER,
            ability=ability,
            render_page=render_page,
            image_path="pijak.png",
            route="pijak",
        )

        self.description = (
            "Zaczynasz grę wiedząc, że 1 z 2 graczy jest konkretną postacią Mieszczanina. "
            "Praczka dowiaduje się, że dana postać Mieszczanina jest w grze, "
            "ale nie wie, który gracz ją posiada."
        )

    def evaluate_knowledge_score(self, player) -> float:
        """Evaluate knowledge score based on the information they have."""
        return player.additional_characters[0].evaluate_knowledge_score(player)
