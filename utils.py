"""Module for handling utility functions and classes in the Mafia game."""
from functools import wraps
from threading import Lock

from flask import redirect, session, url_for

from database import GAME_STATE
from logger import log_info
from state_machine import GAME_SM


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


PAGE_CONFIG = {}
event_id_generator = EventIDGenerator()


def get_state():
    """Handle get state."""
    log_info(f"Current SM state: {GAME_SM.state}")
    return GAME_SM.state


def require_state(required_state):
    """Handle require state."""
    log_info(f"Validate required states: {required_state}")

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            """Handle wrapper."""
            current_state = get_state()

            if current_state != required_state:
                # przekierowanie do właściwego endpointu
                return redirect(url_for(f"state_{current_state}"))

            return f(*args, **kwargs)

        return wrapper

    return decorator


def page_configuration():
    """
    Page configuration.

    Funkcja śledzi zmiany w GAME_STATE i aktualizuje konfigurację strony dla użytkowników.
    Jeśli stan gry zadeklarowany w page_config się zmieni, generuje nowe event_id,
    które może być używane do odświeżenia strony po stronie klienta.
    Dzięki temu klient może aktualizować interfejs użytkownika odpowiednio do aktualnego stanu.
    """
    page_config = {
        "url": url_for(f"state_{GAME_SM.state}"),
        "no_of_players": len(GAME_STATE.players),
    }

    if session.get("client_id") not in [
        player.client_id for player in GAME_STATE.players
    ]:
        log_info("Unknown client accessing page configuration, redirecting to index.")
        page_config["url"] = url_for("index")

    previous_values = (
        {key: value for key, value in PAGE_CONFIG.items() if key != "event_id"}
        if PAGE_CONFIG
        else None
    )
    has_changed = not PAGE_CONFIG or previous_values != page_config

    if has_changed:
        event_id = event_id_generator.next()
    else:
        event_id = PAGE_CONFIG.get("event_id")

    page_config["event_id"] = event_id
    PAGE_CONFIG.update(page_config)

    if has_changed:
        log_info(f"Page configuration: {page_config}")

    return page_config
