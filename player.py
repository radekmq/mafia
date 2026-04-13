"""Module for handling the player definitions in the Mafia game."""

from enum import Enum

from characters.character import Character


class PlayerStatus(Enum):
    """Enum for player status."""

    ALIVE = "alive"
    DEAD = "dead"


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
        self.night_action_done = False

    def reset_status(self):
        """Handle reset status."""
        self.alive = PlayerStatus.ALIVE
        self.poisoned = False
        self.drunk = False
        self.protected = False
        self.additional_characters = []
        self.player_status = None
        self.night_action_done = False
