"""Module for handling the player definitions in the Mafia game."""

import threading
from enum import Enum

from logger import log_info


class PlayerStatus(Enum):
    """Enum for player status."""

    ALIVE = "alive"
    DEAD = "dead"


class PlayerVoteStatus(Enum):
    NOT_VOTED = " - "
    VOTED_YES = "ZAGŁOSOWAŁ TAK"
    VOTED_NO = "WSTRZYMAŁ SIĘ OD GŁOSU"
    NO_RIGHT_TO_VOTE = "NIE MA PRAWA GŁOSU"


# pylint: disable=too-many-instance-attributes,too-many-arguments,too-many-positional-arguments
class Player:
    """Class representing a player."""

    def __init__(
        self,
        client_id: int,
        seat_no: int,
        name: str,
        is_admin: bool = False,
    ):
        """Handle init."""
        self.name = name
        self.seat_no = seat_no
        self.client_id = client_id
        self.is_admin = is_admin
        self.socket_id = None

        # Internal parameters
        self.character = None
        self.alive = PlayerStatus.ALIVE
        self.poisoned = False
        self.drunk = False
        self.protected = False
        self.executed = False
        self.additional_characters = []
        self.player_status = None
        self.vote_status = PlayerVoteStatus.NOT_VOTED
        self.confirm_night_action_done = False
        self.lock = threading.Lock()
        self.active_screen = {"screen": "lobby", "character_data": None}
        self.nominated_for_execution = False
        self.last_vote = True
        self.number_of_votes = 0

    def reset_status(self):
        """Handle reset status."""
        self.alive = PlayerStatus.ALIVE
        self.poisoned = False
        self.drunk = False
        self.protected = False
        self.executed = False
        self.additional_characters = []
        self.player_status = None
        self.confirm_night_action_done = False
        self.vote_status = PlayerVoteStatus.NOT_VOTED
        self.character = None
        self.last_vote = True

    def set_vote_status(self, vote_status: PlayerVoteStatus):
        """Set vote status."""
        with self.lock:
            self.vote_status = vote_status
            if (
                self.alive == PlayerStatus.DEAD
                and vote_status == PlayerVoteStatus.VOTED_YES
            ):
                log_info(
                    f"Player {self.name} is dead and used it's last vote. Setting vote status to YES."
                )
                self.last_vote = False

    def get_vote_status(self) -> PlayerVoteStatus:
        """Get vote status."""
        with self.lock:
            return self.vote_status

    def reset_vote_status(self):
        """Reset vote status."""
        with self.lock:
            self.vote_status = PlayerVoteStatus.NOT_VOTED

    def confirm_night_action(self):
        """Confirm night action."""
        with self.lock:
            self.confirm_night_action_done = True

    def reset_night_action_done(self):
        """Reset night action done status."""
        with self.lock:
            self.confirm_night_action_done = False

    def is_night_action_done(self) -> bool:
        """Check if night action is done."""
        with self.lock:
            return self.confirm_night_action_done

    def set_poisoned(self, poisoned: bool):
        """Set poisoned status."""
        with self.lock:
            self.poisoned = poisoned

    def reset_poisoned(self):
        """Reset poisoned status."""
        with self.lock:
            self.poisoned = False

    def set_protected(self, protected: bool):
        """Set protected status."""
        with self.lock:
            self.protected = protected

    def reset_protected(self):
        """Reset protected status."""
        with self.lock:
            self.protected = False

    def imp_kills_player(self):
        """Handle player death by Imp."""
        with self.lock:
            if not self.protected:
                self.alive = PlayerStatus.DEAD
                log_info(f"Player {self.name} was killed by the Imp.")
            else:
                log_info(
                    f"Player {self.name} was protected and survived the Imp's attack."
                )

    def player_execution(self):
        """Handle player execution."""
        with self.lock:
            self.alive = PlayerStatus.DEAD
            self.executed = True
            log_info(f"Player {self.name} was executed.")

    def reset_night_phase_variables(self):
        """Reset night phase variables."""
        self.reset_poisoned()
        self.reset_protected()
        self.reset_night_action_done()
        self.reset_no_of_votes()

    def set_socket_id(self, socket_id: str):
        """Set socket id."""
        with self.lock:
            self.socket_id = socket_id

    def is_alive(self) -> bool:
        """Check if player is alive."""
        with self.lock:
            return self.alive == PlayerStatus.ALIVE

    def is_administrator(self) -> bool:
        """Check if player is admin."""
        with self.lock:
            return self.is_admin

    def set_active_screen(self, screen_name: str):
        """Set active screen."""
        with self.lock:
            self.active_screen = screen_name

    def is_nominated_for_execution(self) -> bool:
        """Check if player is nominated for execution."""
        with self.lock:
            return self.nominated_for_execution

    def set_nominated_for_execution(self, nominated: bool):
        """Set nominated for execution status."""
        with self.lock:
            self.nominated_for_execution = nominated

    def reset_last_vote(self):
        """Reset last vote status."""
        with self.lock:
            self.last_vote = True

    def has_last_vote(self) -> bool:
        """Check if player has last vote."""
        with self.lock:
            return self.last_vote

    def reset_no_of_votes(self):
        """Reset number of votes."""
        with self.lock:
            self.number_of_votes = 0

    def increase_no_of_votes(self) -> int:
        """Increase number of votes by 1 and return the new value."""
        with self.lock:
            self.number_of_votes += 1
            return self.number_of_votes

    def get_no_of_votes(self) -> int:
        """Get number of votes."""
        with self.lock:
            return self.number_of_votes

    def set_player_executed(self):
        """Set player executed status."""
        with self.lock:
            self.executed = True

    def is_player_executed(self) -> bool:
        """Check if player has been executed."""
        with self.lock:
            return self.executed
