"""Module for handling utility functions and classes in the Mafia game."""
from functools import wraps
from threading import Lock

from flask import redirect, session, url_for

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


def require_state(required_state):
    """Handle require state."""

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            """Handle wrapper."""
            log_info(f"Validate required states: {required_state}")
            from state_machine import CLOCKTOWER_GAME

            current_state = CLOCKTOWER_GAME.state

            if current_state != required_state:
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
        "day_discussions": "DZIEŃ – dyskusja",
        "nomination_and_voting": "DZIEŃ - Nominacje i głosowanie",
        "execution": "DZIEŃ - Egzekucja",
        "game_over": "Koniec gry",
    }
    return descriptions[game_state]
