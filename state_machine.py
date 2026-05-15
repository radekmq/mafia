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

    def on_enter_initial_game_score_calculation(self):
        """Handle on enter calculate game score."""
        log_info("[SM on enter] Obliczanie wyniku gry")

        event = Event(
            name="enter_game_score_calculation",
            actor_id="SYSTEM",
        )
        self.dispatcher.enqueue_event(event)

    def on_enter_night_resolution_game_score_calculation(self):
        """Handle on enter calculate game score."""
        log_info("[SM on enter] Obliczanie wyniku gry")

        event = Event(
            name="enter_game_score_calculation",
            actor_id="SYSTEM",
        )
        self.dispatcher.enqueue_event(event)

    # =========================
    # HOOKI (EXIT)
    # =========================

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
    "initial_game_score_calculation",
    "night_resolution_game_score_calculation",
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
        "dest": "initial_game_score_calculation",
    },
    {
        "trigger": "game_score_calculated",
        "source": "initial_game_score_calculation",
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
        "dest": "night_resolution_game_score_calculation",
    },
    {
        "trigger": "game_score_calculated",
        "source": "night_resolution_game_score_calculation",
        "dest": "day_discussions",
    },
    # DZIEŃ
    {
        "trigger": "next_phase",
        "source": "day_discussions",
        "dest": "nomination",
    },
    {
        "trigger": "virgin_executed",
        "source": "nomination",
        "dest": "execution",
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
