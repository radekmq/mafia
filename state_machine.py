"""Module for handling the state machine of the Mafia game."""


from game_events import Event
from logger import log_info


class StateMachine:
    """Handle the state machine for the Clocktower game."""

    def __init__(self):
        """Handle init."""
        # transitions.Machine nadpisuje ten atrybut podczas inicjalizacji FSM.
        self.state = "lobby"
        self.dispatcher = None

    def register_dispatcher(self, dispatcher):
        """Register dispatcher."""
        self.dispatcher = dispatcher

    # =========================
    # HOOKI (ENTER)
    # =========================

    def on_enter_lobby(self):
        """Handle on enter lobby."""
        log_info("[SM on enter] Lobby – oczekiwanie na graczy")

        event = Event(
            name="enter_lobby",
            actor_id="SYSTEM",
        )
        self.dispatcher.enqueue_event(event)

    def on_enter_players_introduction(self):
        """Handle on enter players introduction."""
        log_info("[SM on enter] Przedstawienie ról graczy")

        event = Event(
            name="enter_players_introduction",
            actor_id="SYSTEM",
        )
        self.dispatcher.enqueue_event(event)

    def on_enter_night_actions(self):
        """Handle on enter night minion action."""
        log_info("[SM on enter] Noc: Akcje graczy")

        event = Event(
            name="enter_night_actions",
            actor_id="SYSTEM",
        )
        self.dispatcher.enqueue_event(event)

    def on_enter_night_resolving_actions(self):
        """Handle on enter night all players action."""
        log_info("[SM on enter] Noc: Rozpatrzenie akcji")

        event = Event(
            name="enter_night_resolution",
            actor_id="SYSTEM",
        )
        self.dispatcher.enqueue_event(event)

    def on_enter_night_summary(self):
        """Handle on enter night presentations."""
        log_info("[SM on enter] Noc: Podsumowanie")

    def on_enter_day_discussions(self):
        """Handle on enter day discussions."""
        log_info("[SM on enter] Dzień: Dyskusja")

        event = Event(
            name="enter_day_discussions",
            actor_id="SYSTEM",
        )
        self.dispatcher.enqueue_event(event)

    def on_enter_nomination(self):
        """Handle on enter nomination."""
        log_info("[SM on enter] Nominacje")

        event = Event(
            name="enter_day_nomination",
            actor_id="SYSTEM",
        )
        self.dispatcher.enqueue_event(event)

    def on_enter_voting(self):
        """Handle on enter voting."""
        log_info("[SM on enter] Głosowanie")

        event = Event(
            name="enter_day_voting",
            actor_id="SYSTEM",
        )
        self.dispatcher.enqueue_event(event)

    def on_enter_execution(self):
        """Handle on enter execution."""

        event = Event(
            name="enter_day_execution",
            actor_id="SYSTEM",
        )
        self.dispatcher.enqueue_event(event)

    def on_enter_game_over(self):
        """Handle on enter game over."""
        log_info("[SM on enter] KONIEC GRY")

        event = Event(
            name="enter_game_over",
            actor_id="SYSTEM",
        )
        self.dispatcher.enqueue_event(event)

    def on_enter_night_game_conditions(self):
        """Handle on enter night game conditions."""
        log_info("[SM on enter] Noc: Sprawdzanie warunków zakończenia gry")

        event = Event(
            name="enter_game_conditions_resolution",
            actor_id="SYSTEM",
        )
        self.dispatcher.enqueue_event(event)

    def on_enter_day_game_conditions(self):
        """Handle on enter day game conditions."""
        log_info("[SM on enter] Dzień: Sprawdzanie warunków zakończenia gry")

        event = Event(
            name="enter_game_conditions_resolution",
            actor_id="SYSTEM",
        )
        self.dispatcher.enqueue_event(event)

    # =========================
    # HOOKI (EXIT)
    # =========================

    def on_exit_lobby(self):
        """Handle on exit lobby."""
        log_info("[SM on exit] Start gry")

    def on_exit_players_introduction(self):
        """Handle on exit players introduction."""
        log_info("[SM on exit] Zakończono przedstawienie")

    def on_exit_night_actions(self):
        """Handle on exit night minion action."""
        log_info("[SM on exit] NOC: Akcje graczy zakończone")

    def on_exit_night_resolving_actions(self):
        """Handle on exit night all players action."""
        log_info("[SM on exit] NOC: Rozpatrzenie akcji zakończone")

    def on_exit_night_summary(self):
        """Handle on exit night presentations."""
        log_info("[SM on exit] Zakończono prezentacje nocne")

    def on_exit_day_discussions(self):
        """Handle on exit day discussions."""
        log_info("[SM on exit] Koniec dyskusji")

    def on_exit_nomination(self):
        """Handle on exit nomination."""
        log_info("[SM on exit] Koniec nominacji")

    def on_exit_voting(self):
        """Handle on exit voting."""
        log_info("[SM on exit] Koniec głosowania")

    def on_exit_execution(self):
        """Handle on exit execution."""
        log_info("[SM on exit] Zakończono egzekucję")

    def on_exit_night_game_conditions(self):
        """Handle on exit night game conditions."""
        log_info("[SM on exit] Noc: Zakończono sprawdzanie warunków zakończenia gry")

    def on_exit_day_game_conditions(self):
        """Handle on exit day game conditions."""
        log_info("[SM on exit] Dzień: Zakończono sprawdzanie warunków zakończenia gry")

    def on_exit_game_over(self):
        """Handle on exit game over."""
        log_info("[SM on exit] KONIEC GRY")

        event = Event(
            name="exit_game_over",
            actor_id="SYSTEM",
        )
        self.dispatcher.enqueue_event(event)

    # =========================
    # JEDYNY WARUNEK
    # =========================

    def should_end_game(self):
        """Zaimplementujesz: warunki zwycięstwa (Imp vs Town)."""
        cond_met = self.dispatcher.game_state.game_over_conditions_met
        if not cond_met:
            pass
        log_info(f"[SM] Warunek zakończenia gry {cond_met} został spełniony!")
        return cond_met


# =========================
# DEFINICJA FSM
# =========================

states = [
    "lobby",
    "players_introduction",
    "night_actions",
    "night_resolving_actions",
    "night_game_conditions",
    "day_discussions",
    "nomination",
    "voting",
    "execution",
    "day_game_conditions",
    "game_over",
]

transitions = [
    # START
    {
        "trigger": "next_phase",
        "source": "lobby",
        "dest": "players_introduction",
    },
    {
        "trigger": "next_phase",
        "source": "players_introduction",
        "dest": "night_actions",
    },
    # NOC
    {
        "trigger": "next_phase",
        "source": "night_actions",
        "dest": "night_resolving_actions",
    },
    {
        "trigger": "next_phase",
        "source": "night_resolving_actions",
        "dest": "night_game_conditions",
    },
    {
        "trigger": "all_conditions_resolved",
        "source": "night_game_conditions",
        "dest": "game_over",
        "conditions": "should_end_game",
    },
    {
        "trigger": "all_conditions_resolved",
        "source": "night_game_conditions",
        "dest": "day_discussions",
    },
    # DZIEŃ
    {
        "trigger": "next_phase",
        "source": "day_discussions",
        "dest": "nomination",
    },
    {
        "trigger": "next_phase",
        "source": "nomination",
        "dest": "voting",
    },
    {
        "trigger": "next_phase",
        "source": "voting",
        "dest": "nomination",
    },
    {
        "trigger": "start_execution_phase",
        "source": "nomination",
        "dest": "execution",
    },
    {
        "trigger": "next_phase",
        "source": "execution",
        "dest": "day_game_conditions",
    },
    # 👉 ZNOWU: najpierw game_over
    {
        "trigger": "all_conditions_resolved",
        "source": "day_game_conditions",
        "dest": "game_over",
        "conditions": "should_end_game",
    },
    {
        "trigger": "all_conditions_resolved",
        "source": "day_game_conditions",
        "dest": "night_actions",
    },
    {
        "trigger": "next_phase",
        "source": "game_over",
        "dest": "lobby",
    },
]


# =========================
# UTILS
# =========================
