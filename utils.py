"""Module for handling utility functions and classes in the Mafia game."""
from functools import wraps
from threading import Lock

from flask import redirect, session, url_for

from characters.character import RoleType
from logger import log_info


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


def require_state(required_states):
    """Handle require state."""

    if isinstance(required_states, str):
        required_states = [required_states]

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            """Handle wrapper."""
            log_info(f"Validate required states: {required_states}")
            from state_machine import CLOCKTOWER_GAME

            current_state = CLOCKTOWER_GAME.state

            if current_state not in required_states:
                # przekierowanie do właściwego endpointu
                return redirect(url_for(f"state_{current_state}"))

            return f(*args, **kwargs)

        return wrapper

    return decorator


def user_in_play(f):
    """Ensure the current user belongs to the active game before entering a view."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        """Handle wrapper."""
        log_info("Validate if user is in play.")
        from state_machine import CLOCKTOWER_GAME

        client_id = session.get("client_id")
        player = CLOCKTOWER_GAME.game_state.get_player_by_client_id(client_id)

        if not (client_id and player):
            if CLOCKTOWER_GAME.game_state.game_ongoing:
                log_info(
                    "User in ongoing game without client_id, redirect to game_ongoing."
                )
                return redirect(url_for("game_ongoing"))
            log_info("User in game without client_id, redirect to index.")
            return redirect(url_for("index"))

        return f(*args, **kwargs)

    return wrapper


def get_state_description(game_state):
    """Handle get state description."""
    descriptions = {
        "lobby": "Lobby – oczekiwanie na graczy",
        "players_introduction": "Wprowadzenie postaci",
        "night_minion_action": "NOC – akcja minionów",
        "night_all_players_action": "NOC – akcje wszystkich graczy",
        "night_summary": "NOC – podsumowanie nocy",
        "day_discussions": "DZIEŃ – dyskusja",
        "nomination": "DZIEŃ - nominacja",
        "voting": "DZIEŃ - głosowanie",
        "execution": "DZIEŃ - egzekucja",
        "game_over": "Koniec gry",
    }
    return descriptions[game_state]


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
