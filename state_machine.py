"""Module for handling the state machine of the Mafia game."""

from flask import session, url_for
from transitions import Machine

from game_state import GameState
from logger import log_info
from state_machine_utils import assign_random_characters, log_players_status_table
from utils import EventIDGenerator


class ClocktowerGame:
    """Handle the state machine for the Clocktower game."""

    def __init__(self):
        """Handle init."""
        # transitions.Machine nadpisuje ten atrybut podczas inicjalizacji FSM.
        self.state = "lobby"
        self.day_number = 0
        self.execution_count = 0
        self.game_state = GameState()

        # Wewnętrzna konfiguracja
        self._page_config = {}
        self._event_id_generator = EventIDGenerator()

    # =========================
    # HOOKI (ENTER)
    # =========================

    def on_enter_lobby(self):
        """Handle on enter lobby."""
        log_info("[SM on enter] Lobby – oczekiwanie na graczy")

    def on_enter_players_introduction(self):
        """Handle on enter players introduction."""
        log_info("[SM on enter] Przedstawienie ról graczy")
        self.game_state.game_ongoing = True
        assign_random_characters(self.game_state)
        self.game_state.get_current_player().character.ability.setup(self)
        log_players_status_table(self.game_state)

    def on_enter_night_minion_action(self):
        """Handle on enter night minion action."""
        log_info("[SM on enter] Noc – akcje złych (Imp + miniony)")
        log_players_status_table(self.game_state)

    def on_enter_night_all_players_action(self):
        """Handle on enter night all players action."""
        log_info("[SM on enter] Noc – akcje wszystkich postaci")
        log_players_status_table(self.game_state)

    def on_enter_day_discussions(self):
        """Handle on enter day discussions."""
        self.day_number += 1
        log_info(f"[SM on enter] Dzień {self.day_number} – dyskusja")
        log_players_status_table(self.game_state)

    def on_enter_nomination_and_voting(self):
        """Handle on enter nomination and voting."""
        log_info("[SM on enter] Nominacje i głosowanie")

    def on_enter_execution(self):
        """Handle on enter execution."""
        self.execution_count += 1
        log_info(f"[SM on enter] Egzekucja nr {self.execution_count}")

    def on_enter_game_over(self):
        """Handle on enter game over."""
        log_info("[SM on enter] KONIEC GRY")

    # =========================
    # HOOKI (EXIT)
    # =========================

    def on_exit_lobby(self):
        """Handle on exit lobby."""
        log_info("[SM on exit] Start gry")
        self.game_state.reset_game()

    def on_exit_players_introduction(self):
        """Handle on exit players introduction."""
        log_info("[SM on exit] Zakończono przedstawienie")

    def on_exit_night_minion_action(self):
        """Handle on exit night minion action."""
        log_info("[SM on exit] Złe postacie wykonały akcje")

    def on_exit_night_all_players_action(self):
        """Handle on exit night all players action."""
        log_info("[SM on exit] Wszystkie akcje nocne zakończone")

    def on_exit_day_discussions(self):
        """Handle on exit day discussions."""
        log_info("[SM on exit] Koniec dyskusji")

    def on_exit_nomination_and_voting(self):
        """Handle on exit nomination and voting."""
        log_info("[SM on exit] Koniec głosowania")

    def on_exit_execution(self):
        """Handle on exit execution."""
        log_info("[SM on exit] Zakończono egzekucję")

    # =========================
    # JEDYNY WARUNEK
    # =========================

    def should_end_game(self):
        """Zaimplementujesz: warunki zwycięstwa (Imp vs Town)."""
        log_info("[SM] Sprawdzanie warunków zakończenia gry")
        return False  # Placeholder, implement actual win conditions here

    def page_configuration(self):
        """
        Page configuration.

        Funkcja śledzi zmiany w grze i aktualizuje konfigurację strony dla użytkowników.
        Jeśli stan gry zadeklarowany w page_config się zmieni, generuje nowe event_id,
        które może być używane do odświeżenia strony po stronie klienta.
        Dzięki temu klient może aktualizować interfejs użytkownika odpowiednio do aktualnego stanu.
        """
        page_config = {
            "url": url_for(f"state_{self.state}"),
            "no_of_players": len(self.game_state.players),
        }

        if session.get("client_id") not in [
            player.client_id for player in self.game_state.players
        ]:
            log_info(
                "Unknown client accessing page configuration, redirecting to index."
            )
            page_config["url"] = url_for("index")

        previous_values = (
            {
                key: value
                for key, value in self._page_config.items()
                if key != "event_id"
            }
            if self._page_config
            else None
        )
        has_changed = not self._page_config or previous_values != page_config

        if has_changed:
            event_id = self._event_id_generator.next()
        else:
            event_id = self._page_config.get("event_id")

        page_config["event_id"] = event_id
        self._page_config.update(page_config)

        if has_changed:
            log_info(f"Page configuration: {page_config}")

        return page_config


# =========================
# DEFINICJA FSM
# =========================

states = [
    "lobby",
    "players_introduction",
    "night_minion_action",
    "night_all_players_action",
    "day_discussions",
    "nomination_and_voting",
    "execution",
    "game_over",
]

transitions = [
    # START
    {
        "trigger": "start_introduction",
        "source": "lobby",
        "dest": "players_introduction",
    },
    {
        "trigger": "start_evil_night_actions",
        "source": "players_introduction",
        "dest": "night_minion_action",
    },
    # NOC
    {
        "trigger": "start_all_players_night_actions",
        "source": "night_minion_action",
        "dest": "night_all_players_action",
    },
    # 👉 PRIORYTET: najpierw sprawdzamy game_over
    {
        "trigger": "all_night_actions_done",
        "source": "night_all_players_action",
        "dest": "game_over",
        "conditions": "should_end_game",
    },
    {
        "trigger": "all_night_actions_done",
        "source": "night_all_players_action",
        "dest": "day_discussions",
    },
    # DZIEŃ
    {
        "trigger": "start_voting_phase",
        "source": "day_discussions",
        "dest": "nomination_and_voting",
    },
    {
        "trigger": "voting_finished",
        "source": "nomination_and_voting",
        "dest": "execution",
    },
    # 👉 ZNOWU: najpierw game_over
    {
        "trigger": "execution_finished",
        "source": "execution",
        "dest": "game_over",
        "conditions": "should_end_game",
    },
    {
        "trigger": "execution_finished",
        "source": "execution",
        "dest": "night_minion_action",
    },
]


# =========================
# INICJALIZACJA
# =========================

CLOCKTOWER_GAME = ClocktowerGame()

STATE_MACHINE = Machine(
    model=CLOCKTOWER_GAME,
    states=states,
    transitions=transitions,
    initial="lobby",
    auto_transitions=False,
)
