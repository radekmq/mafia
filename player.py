"""Module for handling the player definitions in the Mafia game."""

import threading
from enum import Enum

from characters.character import Character


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
        character: Character | None = None,
        alive: PlayerStatus = PlayerStatus.ALIVE,
        poisoned: bool = False,
        drunk: bool = False,
        protected: bool = False,
        additional_characters: list[Character] | None = None,
        is_admin: bool = False,
    ):
        """Handle init."""
        self.name = name
        self.character = character
        self.alive = alive
        self.poisoned = poisoned
        self.drunk = drunk
        self.protected = protected
        self.additional_characters = additional_characters or []
        self.is_admin = is_admin
        self.seat_no = seat_no
        self.client_id = client_id

        # Internal parameters
        self.player_status = None
        self.vote_status = PlayerVoteStatus.NOT_VOTED
        self.night_action_done = False
        self.admin_confirm_action = False
        self.minion_confirm_action = False
        self.lock = threading.Lock()

    def reset_status(self):
        """Handle reset status."""
        self.alive = PlayerStatus.ALIVE
        self.poisoned = False
        self.drunk = False
        self.protected = False
        self.additional_characters = []
        self.player_status = None
        self.night_action_done = False
        self.admin_confirm_action = False
        self.minion_confirm_action = False

    def set_vote_status(self, vote_status: PlayerVoteStatus):
        """Set vote status."""
        with self.lock:
            self.vote_status = vote_status

    def get_vote_status(self) -> PlayerVoteStatus:
        """Get vote status."""
        with self.lock:
            return self.vote_status

    def reset_vote_status(self):
        """Reset vote status."""
        with self.lock:
            self.vote_status = PlayerVoteStatus.NOT_VOTED

    def confirm_admin_action(self):
        """Confirm admin action."""
        with self.lock:
            self.admin_confirm_action = True

    def reset_admin_confirmation(self):
        """Reset admin confirmation."""
        with self.lock:
            self.admin_confirm_action = False

    def is_admin_action_confirmed(self) -> bool:
        """Check if admin action is confirmed."""
        with self.lock:
            return self.admin_confirm_action

    def confirm_minion_action(self):
        """Confirm minion action."""
        with self.lock:
            self.minion_confirm_action = True

    def reset_minion_confirmation(self):
        """Reset minion confirmation."""
        with self.lock:
            self.minion_confirm_action = False

    def is_minion_action_confirmed(self) -> bool:
        """Check if minion action is confirmed."""
        with self.lock:
            return self.minion_confirm_action
