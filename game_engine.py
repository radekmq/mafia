from transitions import Machine

from characters.trouble_brewing_setup import TroubleBrewingScenario
from dispatcher import Dispatcher
from game_events import Event
from game_state import GameState
from heuristics_recluse import RecluseHeuristic
from heuristics_winner import WinnerHeuristic
from state_machine import StateMachine, states, transitions
from utils import EventIDGenerator


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
        self.winner_heuristic = WinnerHeuristic(
            self.game_state, self.game_setup.character_power
        )
        self.recluse_heuristic = RecluseHeuristic(
            self.game_state, self.winner_heuristic
        )
        self.game_setup.set_recluse_heuristic(self.recluse_heuristic)

        self.dispatcher = Dispatcher(
            self.game_state, self.state_machine, self.game_setup, self.recluse_heuristic
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
