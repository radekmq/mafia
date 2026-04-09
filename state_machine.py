"""Module for handling the state machine of the Mafia game."""

from transitions import Machine

from database import GAME_STATE
from logger import log_info
from state_machine_utils import assign_random_characters, log_players_status_table


class ClocktowerGame:
    """Handle the state machine for the Clocktower game."""

    def __init__(self):
        """Handle init."""
        # transitions.Machine nadpisuje ten atrybut podczas inicjalizacji FSM.
        self.state = "lobby"
        self.day_number = 0
        self.execution_count = 0

    # =========================
    # HOOKI (ENTER)
    # =========================

    def on_enter_lobby(self):
        """Handle on enter lobby."""
        log_info("[SM on enter] Lobby – oczekiwanie na graczy")

    def on_enter_players_introduction(self):
        """Handle on enter players introduction."""
        log_info("[SM on enter] Przedstawienie ról graczy")
        GAME_STATE.game_ongoing = True
        assign_random_characters()
        log_players_status_table()

    def on_enter_night_minion_action(self):
        """Handle on enter night minion action."""
        log_info("[SM on enter] Noc – akcje złych (Imp + miniony)")
        log_players_status_table()

    def on_enter_night_all_players_action(self):
        """Handle on enter night all players action."""
        log_info("[SM on enter] Noc – akcje wszystkich postaci")
        log_players_status_table()

    def on_enter_day_discussions(self):
        """Handle on enter day discussions."""
        self.day_number += 1
        log_info(f"[SM on enter] Dzień {self.day_number} – dyskusja")
        log_players_status_table()

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
        GAME_STATE.reset_game()

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
        "trigger": "start_first_night",
        "source": "players_introduction",
        "dest": "night_minion_action",
    },
    # NOC
    {
        "trigger": "minions_done",
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


def get_state_description(state):
    """Handle get state description."""
    descriptions = {
        "lobby": "Lobby – oczekiwanie na graczy",
        "players_introduction": "Wprowadzenie postaci",
        "night_minion_action": "NOC – akcje złych (Imp + miniony)",
        "night_all_players_action": "NOC – akcje wszystkich postaci",
        "day_discussions": "DZIEŃ – dyskusja",
        "nomination_and_voting": "DZIEŃ - Nominacje i głosowanie",
        "execution": "DZIEŃ - Egzekucja",
        "game_over": "Koniec gry",
    }
    return descriptions[state]


# =========================
# INICJALIZACJA
# =========================

GAME_SM = ClocktowerGame()

STATE_MACHINE = Machine(
    model=GAME_SM,
    states=states,
    transitions=transitions,
    initial="lobby",
    auto_transitions=False,
)
