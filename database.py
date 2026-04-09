"""Module for handling the game state and character definitions in the Mafia game."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from characters import (
    fun_bibliotekarka,
    fun_detektyw,
    fun_empata,
    fun_grabarz,
    fun_imp,
    fun_jasnowidz,
    fun_kucharz,
    fun_pijak,
    fun_truciciel,
)


class RoleType(Enum):
    """Enum for role type."""

    TOWNSFOLK = "townsfolk"
    OUTSIDER = "outsider"
    MINION = "minion"
    DEMON = "demon"


class PlayerStatus(Enum):
    """Enum for player status."""

    ALIVE = "alive"
    DEAD = "dead"


@dataclass
class Ability:
    """Class representing an ability."""

    description: str
    effect: Callable[..., str]


@dataclass
class Character:
    """Class representing a character."""

    name: str
    role_type: RoleType
    ability: Ability = field(repr=False)
    image_path: str
    route: str


DB_CHARACTERS = {
    # ====== MIESZKAŃCY ======
    "bibliotekarka": Character(
        name="Bibliotekarka",
        role_type=RoleType.TOWNSFOLK,
        ability=Ability(
            description=(
                "Na początku wiesz, że 1 z 2 graczy jest konkretnym Outsiderem "
                "(lub że żaden nie jest w grze). Bibliotekarka dowiaduje się, "
                "że konkretny Outsider jest w grze, ale nie kto go gra."
            ),
            effect=fun_bibliotekarka,
        ),
        image_path="bibliotekarka.png",
        route="bibliotekarka",
    ),
    "detektyw": Character(
        name="Detektyw",
        role_type=RoleType.TOWNSFOLK,
        ability=Ability(
            description=(
                "Na początku wiesz, że 1 z 2 graczy jest konkretnym Minionem. "
                "Detektyw dowiaduje się, że konkretny Minion jest w grze, "
                "ale nie kto go gra."
            ),
            effect=fun_detektyw,
        ),
        image_path="detektyw.png",
        route="detektyw",
    ),
    "kucharz": Character(
        name="Kucharz",
        role_type=RoleType.TOWNSFOLK,
        ability=Ability(
            description=(
                "Na początku wiesz, ile par złych graczy siedzi obok siebie. "
                "Kucharz wie, czy źli gracze siedzą obok siebie."
            ),
            effect=fun_kucharz,
        ),
        image_path="kucharz.png",
        route="kucharz",
    ),
    "empata": Character(
        name="Empata",
        role_type=RoleType.TOWNSFOLK,
        ability=Ability(
            description=(
                "Po każdej nocy Empata dowiaduje się, ilu z jego dwóch "
                "żyjących sąsiadów jest złych. Empata uczy się, "
                "czy sąsiadujący z nim gracze są dobrzy czy źli."
            ),
            effect=fun_empata,
        ),
        image_path="empata.png",
        route="empata",
    ),
    "jasnowidz": Character(
        name="Jasnowidz",
        role_type=RoleType.TOWNSFOLK,
        ability=Ability(
            description=(
                "Po każdej nocy wybierz 2 graczy: dowiadujesz się, "
                "czy którykolwiek z nich jest Demonem. Jasnowidz dowiaduje się, "
                "czy którykolwiek z dwóch graczy jest Demonem."
            ),
            effect=fun_jasnowidz,
        ),
        image_path="jasnowidz.png",
        route="jasnowidz",
    ),
    "grabarz": Character(
        name="Grabarz",
        role_type=RoleType.TOWNSFOLK,
        ability=Ability(
            description="Każdej nocy dowiadujesz się, jaka postać została dziś stracona.",
            effect=fun_grabarz,
        ),
        image_path="grabarz.png",
        route="grabarz",
    ),
    "pijak": Character(
        name="Pijak",
        role_type=RoleType.OUTSIDER,
        ability=Ability(
            description=(
                "Nie wiesz, że jesteś Pijakiem. Myślisz, że jesteś "
                "postacią z grupy Townsfolk, ale nią nie jesteś."
            ),
            effect=fun_pijak,
        ),
        image_path="pijak.png",
        route="pijak",
    ),
    # ====== MINIONKI ======
    "truciciel": Character(
        name="Truciciel",
        role_type=RoleType.MINION,
        ability=Ability(
            description=(
                "Każdej nocy wybierz gracza: tej nocy i następnego dnia "
                "ten gracz jest zatruty. Truciciel potajemnie zakłóca "
                "działanie zdolności postaci."
            ),
            effect=fun_truciciel,
        ),
        image_path="truciciel.png",
        route="truciciel",
    ),
    # ===== DEMONY ======
    "imp": Character(
        name="Imp",
        role_type=RoleType.DEMON,
        ability=Ability(
            description=(
                "Każdej nocy, wybierz gracza: ten gracz umiera. "
                "Jeśli w ten sposób zabijesz samego siebie, jeden z Minionów "
                "staje się Impem. Imp zabija jednego gracza każdej nocy "
                "i może stworzyć kopię samego siebie za straszną cenę."
            ),
            effect=fun_imp,
        ),
        image_path="imp.png",
        route="imp",
    ),
}

CHARACTERS_BY_TYPE = {
    "townsfolk": [
        char for char in DB_CHARACTERS.values() if char.role_type == RoleType.TOWNSFOLK
    ],
    "outsider": [
        char for char in DB_CHARACTERS.values() if char.role_type == RoleType.OUTSIDER
    ],
    "minion": [
        char for char in DB_CHARACTERS.values() if char.role_type == RoleType.MINION
    ],
    "demon": [
        char for char in DB_CHARACTERS.values() if char.role_type == RoleType.DEMON
    ],
}

TROUBLE_BREWING_SETUP = [
    # To be deleted
    {"gracze": 1, "Mieszkańcy": 0, "Outsiderzy": 0, "Minionki": 0, "Demon": 1},
    {"gracze": 2, "Mieszkańcy": 2, "Outsiderzy": 0, "Minionki": 0, "Demon": 0},
    {"gracze": 3, "Mieszkańcy": 3, "Outsiderzy": 0, "Minionki": 0, "Demon": 0},
    {"gracze": 4, "Mieszkańcy": 4, "Outsiderzy": 0, "Minionki": 0, "Demon": 0},
    # Up to here
    {"gracze": 5, "Mieszkańcy": 3, "Outsiderzy": 0, "Minionki": 1, "Demon": 1},
    {"gracze": 6, "Mieszkańcy": 3, "Outsiderzy": 1, "Minionki": 1, "Demon": 1},
    {"gracze": 7, "Mieszkańcy": 5, "Outsiderzy": 0, "Minionki": 1, "Demon": 1},
    {"gracze": 8, "Mieszkańcy": 5, "Outsiderzy": 1, "Minionki": 1, "Demon": 1},
    {"gracze": 9, "Mieszkańcy": 5, "Outsiderzy": 2, "Minionki": 1, "Demon": 1},
    {"gracze": 10, "Mieszkańcy": 7, "Outsiderzy": 0, "Minionki": 2, "Demon": 1},
    {"gracze": 11, "Mieszkańcy": 7, "Outsiderzy": 1, "Minionki": 2, "Demon": 1},
    {"gracze": 12, "Mieszkańcy": 7, "Outsiderzy": 2, "Minionki": 2, "Demon": 1},
    {"gracze": 13, "Mieszkańcy": 9, "Outsiderzy": 0, "Minionki": 3, "Demon": 1},
    {"gracze": 14, "Mieszkańcy": 9, "Outsiderzy": 1, "Minionki": 3, "Demon": 1},
    {"gracze": 15, "Mieszkańcy": 9, "Outsiderzy": 2, "Minionki": 3, "Demon": 1},
]


# pylint: disable=too-many-instance-attributes,too-many-arguments,too-many-positional-arguments
class Player:
    """Class representing a player."""

    def __init__(
        self,
        client_id: int,
        seat_no: int,
        name: str,
        character: Character | None = None,
        alive: PlayerStatus = PlayerStatus.ALIVE,
        poisoned: bool = False,
        drunk: bool = False,
        protected: bool = False,
        additional_characters: list[Character] | None = None,
        is_admin: bool = False,
    ):
        """Handle init."""
        self.name = name
        self.character = character
        self.alive = alive
        self.poisoned = poisoned
        self.drunk = drunk
        self.protected = protected
        self.additional_characters = additional_characters or []
        self.is_admin = is_admin
        self.seat_no = seat_no
        self.client_id = client_id

        # Internal parameters
        self._startup_status = None

    def get_startup_status(self):
        """Handle get startup status."""
        if self._startup_status is None:
            self._startup_status = self.character.ability.effect(self)
        return self._startup_status

    def reset_status(self):
        """Handle reset status."""
        self.alive = PlayerStatus.ALIVE
        self.poisoned = False
        self.drunk = False
        self.protected = False
        self.additional_characters = []
        self._startup_status = None


# pylint: disable=too-many-instance-attributes,too-many-arguments,too-many-positional-arguments
class Game:
    """Class representing the game state."""

    def __init__(
        self,
        players: list[Player] | None = None,
        day: int = 0,
        night: int = 0,
        action_truciciel_done: bool = False,
        action_imp_done: bool = False,
        last_executed_player: Player | None = None,
        nominated_by_imp_to_die: Player | None = None,
        kruk_died_last_night: bool = False,
        virgin_nomination_counter: int = 0,
        auto_game: bool = False,
        alive_players_counter: int = 0,
        alive_evil_players_counter: int = 0,
        execute_on_majority: bool = False,
        game_ongoing: bool = False,
    ):
        """Handle init."""
        self.players = players or []
        self.day = day
        self.night = night
        self.action_truciciel_done = action_truciciel_done
        self.action_imp_done = action_imp_done
        self.last_executed_player = last_executed_player
        self.nominated_by_imp_to_die = nominated_by_imp_to_die
        self.kruk_died_last_night = kruk_died_last_night
        self.virgin_nomination_counter = virgin_nomination_counter

        # jeśli True, to gra będzie przebiegać automatycznie, z minimalną interakcją moderatora
        self.auto_game = auto_game

        # ten licznik jest potrzebny do sprawdzania warunku zwycięstwa Mieszkańców
        self.alive_players_counter = alive_players_counter

        # ten licznik jest potrzebny do sprawdzania warunku zwycięstwa Minionów i Demona
        self.alive_evil_players_counter = alive_evil_players_counter

        # jeśli True, to egzekucja w ciągu dnia nastąpi po bezwzględnej większości głosów
        self.execute_on_majority = execute_on_majority

        # czy gra jest w toku, czy zakończyła się zwycięstwem którejś ze stron
        self.game_ongoing = game_ongoing

    # =========================
    # FUNCTIONS OPERATING ON GAME STATE
    # =========================

    def get_player_by_client_id(self, client_id: str) -> Player | None:
        """Handle get player by client id."""
        for player in self.players:
            if player.client_id == client_id:
                return player
        return None

    def get_player_name(self, client_id: str) -> str | None:
        """Handle get player name."""
        player = self.get_player_by_client_id(client_id)
        return player.name if player else None

    def reset_game(self):
        """Handle reset game."""
        self.day = 0
        self.night = 0
        self.action_truciciel_done = False
        self.action_imp_done = False
        self.last_executed_player = None
        self.nominated_by_imp_to_die = None
        self.kruk_died_last_night = False
        self.virgin_nomination_counter = 0
        self.alive_players_counter = 0
        self.alive_evil_players_counter = 0
        for player in self.players:
            player.reset_status()


# =========================
# INICJALIZACJA
# =========================

GAME_STATE = Game()
