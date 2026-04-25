"""Module for handling the game state and character definitions in the Mafia game."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from logger import LOGGER


class RoleType(Enum):
    """Enum for role type."""

    TOWNSFOLK = "townsfolk"
    OUTSIDER = "outsider"
    MINION = "minion"
    DEMON = "demon"
    DEAD = "dead"


@dataclass
class DualEffect:
    original: Optional[Callable[..., Any]] = None
    fake: Optional[Callable[..., Any]] = None
    name: str = "unknown_effect"  # opcjonalnie do logów

    def __call__(self, *args, is_fake: bool = False, **kwargs):
        fn = self.fake if is_fake else self.original

        if fn is None:
            LOGGER.log_info(
                f"[Ability] {self.name} - Niezaimplementowana funkcja "
                f"(is_fake={is_fake})"
            )
            return None

        return fn(*args, **kwargs)


@dataclass
class Ability:
    night_action: DualEffect = field(
        default_factory=lambda: DualEffect(name="night_action")
    )
    setup: DualEffect = field(default_factory=lambda: DualEffect(name="setup"))
    night_resolution: DualEffect = field(
        default_factory=lambda: DualEffect(name="night_resolution")
    )


@dataclass
class RenderPage:
    introduction: DualEffect = field(
        default_factory=lambda: DualEffect(name="introduction")
    )
    night_action: DualEffect = field(
        default_factory=lambda: DualEffect(name="night_action")
    )
    night_resolution: DualEffect = field(
        default_factory=lambda: DualEffect(name="night_resolution")
    )


@dataclass
class Character:
    """Class representing a character."""

    name: str
    role_type: RoleType
    image_path: str
    route: str
    ability: Ability = field(repr=False)
    render_page: RenderPage = field(repr=False)
    description: Optional[str] = None
