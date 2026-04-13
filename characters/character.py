"""Module for handling the game state and character definitions in the Mafia game."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


class RoleType(Enum):
    """Enum for role type."""

    TOWNSFOLK = "townsfolk"
    OUTSIDER = "outsider"
    MINION = "minion"
    DEMON = "demon"


@dataclass
class Ability:
    """Class representing an ability."""

    description: str
    # Returns a rendered lambda function for the character's ability night page
    effect_night_minion: Optional[Callable[..., str]] = None
    effect_night_all_players: Optional[Callable[..., str]] = None
    # Handle Handle callback for the character's ability, called when the player submits their night action
    callback_night: Optional[Callable[..., str]] = None
    # Optional setup function for the character's ability, called once at the start of the game
    setup: Optional[Callable[..., str]] = None
    # Optional function called when the night phase ends
    on_night_exit: Optional[Callable[..., str]] = None


@dataclass
class Character:
    """Class representing a character."""

    name: str
    role_type: RoleType
    ability: Ability = field(repr=False)
    image_path: str
    route: str
