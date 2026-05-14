"""Module for handling utility functions and classes in the Mafia game."""
import random
from threading import Lock

from characters.character import RoleType
from logger import log_error, log_info


# pylint: disable=too-many-locals
def log_players_status_table(game_state):
    """Handle log players status table."""
    players = list(game_state.players)
    if not players:
        log_info("Brak graczy do wyświetlenia w tabeli statusu.")
        return

    headers = [
        "Nazwa gracza",
        "Seat",
        "Postać",
        "Rola",
        "Pijany",
        "Poisoned",
        "Alive",
        "Protected",
        "Dodatkowe postaci",
    ]

    rows = []
    for player in players:
        character_name = player.character.name if player.character else "-"
        additional = (
            ", ".join(char.name for char in (player.additional_characters or [])) or "-"
        )
        drunk = "TAK" if player.drunk else "NIE"
        poisoned = "TAK" if player.poisoned else "NIE"
        protected = "TAK" if player.protected else "NIE"
        alive = (
            player.alive.value.upper()
            if hasattr(player.alive, "value")
            else str(player.alive)
        )

        rows.append(
            [
                player.name,
                player.seat_no,
                character_name,
                player.character.role_type.value if player.character else "-",
                drunk,
                poisoned,
                alive,
                protected,
                additional,
            ]
        )

    widths = [len(header) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(str(value)))

    def format_row(values):
        """Handle format row."""
        return (
            "| "
            + " | ".join(
                str(value).ljust(widths[index]) for index, value in enumerate(values)
            )
            + " |"
        )

    separator = "+-" + "-+-".join("-" * width for width in widths) + "-+"

    table_lines = [separator, format_row(headers), separator]
    for row in rows:
        table_lines.append(format_row(row))
    table_lines.append(separator)

    log_info("Status graczy:\n" + "\n".join(table_lines))


# pylint: disable=too-many-locals,too-many-statements
def assign_random_characters(list_of_players, scenario_setup):
    """Assign random, unique characters to players based on scenario setup."""
    number_of_players = len(list_of_players)
    if number_of_players == 0:
        log_error("Nie można przypisać postaci: brak graczy.")
        return

    setup_for_player_count = next(
        (
            row
            for row in scenario_setup.trouble_brewing_setup
            if row.get("liczba_graczy") == number_of_players
        ),
        None,
    )

    if setup_for_player_count is None:
        message = (
            "Brak konfiguracji Trouble Brewing dla liczby graczy: "
            f"{number_of_players}."
        )
        log_error(message)
        raise ValueError(message)

    role_requirements = {
        RoleType.TOWNSFOLK: setup_for_player_count.get("Mieszkańcy", 0),
        RoleType.OUTSIDER: setup_for_player_count.get("Outsiderzy", 0),
        RoleType.MINION: setup_for_player_count.get("Minionki", 0),
        RoleType.DEMON: setup_for_player_count.get("Demon", 0),
    }

    required_characters_count = sum(role_requirements.values())
    if required_characters_count != number_of_players:
        message = (
            "Niepoprawna konfiguracja scenariusza: liczba postaci "
            f"({required_characters_count}) nie zgadza się z liczbą graczy "
            f"({number_of_players})."
        )
        log_error(message)
        raise ValueError(message)

    scenario_setup.reset_setup()

    selected_characters = []
    for role_type, required_count in role_requirements.items():
        available_characters = scenario_setup.get_list_of_characters_by_type(
            role_type, available_only=True
        )

        if len(available_characters) < required_count:
            message = (
                "Za mało dostępnych postaci typu "
                f"{role_type.value}: wymagane {required_count}, dostępne "
                f"{len(available_characters)}."
            )
            log_error(message)
            raise ValueError(message)

        selected_characters.extend(random.sample(available_characters, required_count))

    if len({character.character.name for character in selected_characters}) != len(
        selected_characters
    ):
        message = "Wylosowano zduplikowane postaci."
        log_error(message)
        raise ValueError(message)

    random.shuffle(selected_characters)

    for player, character in zip(list_of_players, selected_characters):
        player.character = character.character
        character.assigned_in_play += 1

    rows = []
    for player in list_of_players:
        rows.append(
            {
                "Gracz": player.name,
                "Postać": player.character.name if player.character else "-",
                "Typ postaci": (
                    player.character.role_type.value if player.character else "-"
                ),
            }
        )

    log_dicts_table(rows, title="Rozlosowane postaci")


class EventIDGenerator:
    """Thread-safe generator for unique event IDs."""

    def __init__(self, start=0):
        """Handle init."""
        self._value = start
        self._lock = Lock()

    def next(self):
        """Zwraca kolejny, rosnący event_id (thread-safe)."""
        with self._lock:
            self._value += 1
            return self._value

    def current(self):
        """Zwraca aktualny event_id bez zwiększania."""
        with self._lock:
            return self._value


def get_minion_action_status(ct_game):
    """Get minion action status."""
    minion_action_status = "zakończona"
    for player in ct_game.game_state.players:
        if player.character and player.character.role_type == RoleType.MINION:
            if not player.is_minion_action_confirmed():
                minion_action_status = "oczekuje ..."
                break

    return minion_action_status


def log_dicts_table(rows, title: str = "Tabela danych"):
    """Log tabular data through log_info.

    Accepts a list of dictionaries, a single dictionary, or any scalar value.
    """
    if not rows:
        log_info(f"{title}\n(brak danych)")
        return

    if isinstance(rows, dict):
        rows = [rows]
    elif not isinstance(rows, list):
        log_info(f"{title}\n{rows}")
        return

    if not all(isinstance(row, dict) for row in rows):
        log_info(f"{title}\n" + "\n".join(str(row) for row in rows))
        return

    headers = []
    for row in rows:
        for key in row.keys():
            if key not in headers:
                headers.append(str(key))

    normalized_rows = []
    for row in rows:
        normalized_rows.append(
            {
                header: "" if row.get(header) is None else str(row.get(header, ""))
                for header in headers
            }
        )

    column_widths = {
        header: max(
            len(header),
            *(len(normalized_row[header]) for normalized_row in normalized_rows),
        )
        for header in headers
    }

    def format_row(values: list[str]) -> str:
        return (
            "| "
            + " | ".join(
                value.ljust(column_widths[header])
                for header, value in zip(headers, values)
            )
            + " |"
        )

    separator = (
        "+-" + "-+-".join("-" * column_widths[header] for header in headers) + "-+"
    )
    header_row = format_row(headers)
    data_rows = [
        format_row([row[header] for header in headers]) for row in normalized_rows
    ]

    table_lines = [title, separator, header_row, separator, *data_rows, separator]
    log_info("\n".join(table_lines))


def get_state_description(game_state):
    """Handle get state description."""
    descriptions = {
        "lobby": "Lobby – oczekiwanie na graczy",
        "players_introduction": "Wprowadzenie postaci",
        "night_actions": "NOC: Akcje graczy",
        "night_resolving_actions": "NOC: Rozpatrzenie akcji",
        "night_summary": "NOC: Podsumowanie",
        "day_discussions": "DZIEŃ: Dyskusja",
        "nomination": "DZIEŃ: Nominacja",
        "voting": "DZIEŃ: Głosowanie",
        "execution": "DZIEŃ: Egzekucja",
        "game_over": "Koniec gry",
    }
    return descriptions.get(game_state, "Nieznany stan")
