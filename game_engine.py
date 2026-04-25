from flask import session, url_for
from transitions import Machine

from characters.trouble_brewing_setup import TroubleBrewingScenario
from dispatcher import Dispatcher
from game_events import Event
from game_state import GameState
from logger import log_info
from state_machine import StateMachine, states, transitions
from utils import EventIDGenerator, get_minion_action_status, log_dicts_table


class GameEngine:
    """Handle the Blood on the Clocktower game."""

    def __init__(self):
        """Handle init."""
        # transitions.Machine nadpisuje ten atrybut podczas inicjalizacji FSM.
        self.game_state = GameState()
        self.event_id_generator = EventIDGenerator()
        self.state_machine = StateMachine()
        self.game_setup = TroubleBrewingScenario()
        self.event_id_generator = EventIDGenerator()

        self.dispatcher = Dispatcher(
            self.game_state, self.state_machine, self.game_setup
        )
        self.page_config = {}

        Machine(
            model=self.state_machine,
            states=states,
            transitions=transitions,
            initial="lobby",
            auto_transitions=False,
        )

    def enqueue_event(self, event: Event):
        """Enqueue events and dispatch"""
        self.dispatcher.enqueue_event(event)

    def enqueue_events(self, events: list):
        """Enqueue events and dispatch"""
        self.dispatcher.enqueue_events(events)