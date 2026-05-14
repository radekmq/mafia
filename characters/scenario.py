# Game scenario classes
from dataclasses import dataclass

from characters.character import Character, RoleType
from logger import log_info


@dataclass
class CharacterSetup:
    """Class representing a character setup for a game scenario."""

    character: Character
    assigned_in_play: int = 0


class Scenario:
    """Base class for game scenarios."""

    def __init__(self):
        self.list_of_characters = []  # List of CharacterSetup instances

    def add_character(self, character: Character):
        """Add a character to the scenario."""
        self.list_of_characters.append(CharacterSetup(character))

    def reset_setup(self):
        """Reset the assigned_in_play count for each character."""
        log_info("Resetting assigned_in_play for all characters.")
        for character_setup in self.list_of_characters:
            log_info(
                f"Resetting {character_setup.character.name}: {character_setup.assigned_in_play} -> 0"
            )
            character_setup.assigned_in_play = 0

    def get_character_by_route(self, route: str) -> Character:
        """Get a character by its route."""
        for character_setup in self.list_of_characters:
            if character_setup.character.route == route:
                return character_setup.character
        return None

    def is_character_available(self, character: Character) -> bool:
        """Check if a character is available for assignment based on the assigned_in_play count."""
        for character_setup in self.list_of_characters:
            if character_setup.character == character:
                return (
                    character_setup.assigned_in_play < 1
                )  # Assuming we want to limit to 1 assignment per character
        return False  # Character not found in the scenario

    def get_list_of_characters_by_type(
        self, role_types: list, available_only: bool = False
    ) -> list:
        """Get a list of characters in the scenario filtered by role type."""
        if not isinstance(role_types, list):
            role_types = [role_types]
        return_list = []
        if available_only:
            for role_type in role_types:
                return_list.extend(
                    [
                        cs
                        for cs in self.list_of_characters
                        if cs.character.role_type == role_type
                        and cs.assigned_in_play < 1
                    ]
                )
            return return_list
        log_info("Filtering characters by role type.")
        for role_type in role_types:
            log_info(f"Role type: {role_type}")
            for cs in self.list_of_characters:
                log_info(
                    f"Character: {cs.character.name}, Role: {cs.character.role_type}, Assigned: {cs.assigned_in_play}"
                )
            return_list.extend(
                [
                    cs
                    for cs in self.list_of_characters
                    if cs.character.role_type == role_type
                ]
            )
        return return_list

    def get_list_of_unassigned_characters_by_type(self, role_types: list) -> list:
        """Get a list of unassigned characters in the scenario filtered by role type."""
        if not isinstance(role_types, list):
            role_types = [role_types]
        return_list = []
        for role_type in role_types:
            return_list.extend(
                [
                    cs
                    for cs in self.list_of_characters
                    if cs.character.role_type == role_type and cs.assigned_in_play == 0
                ]
            )
        return return_list

    def get_dict_of_characters(self) -> dict:
        """Get a dictionary of characters in the scenario with their assigned_in_play count."""

        CHARACTERS_BY_TYPE = {
            "townsfolk": [
                char.character
                for char in self.list_of_characters
                if char.character.role_type == RoleType.TOWNSFOLK
            ],
            "outsider": [
                char.character
                for char in self.list_of_characters
                if char.character.role_type == RoleType.OUTSIDER
            ],
            "minion": [
                char.character
                for char in self.list_of_characters
                if char.character.role_type == RoleType.MINION
            ],
            "demon": [
                char.character
                for char in self.list_of_characters
                if char.character.role_type == RoleType.DEMON
            ],
        }

        return CHARACTERS_BY_TYPE

    def set_recluse_heuristic(self, heuristic):
        recluse = self.get_character_by_route("pustelnik")
        if recluse:
            recluse.set_recluse_heuristic(heuristic)
