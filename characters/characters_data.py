"""Module for handling the game state and character definitions in the Mafia game."""


from characters.character import RoleType
from characters.character_details.bibliotekarka import BibliotekarkaCharacter
from characters.character_details.detektyw import DetektywCharacter
from characters.character_details.empata import EmpataCharacter
from characters.character_details.imp import ImpCharacter
from characters.character_details.kucharz import KucharzCharacter
from characters.character_details.praczka import PraczkaCharacter
from characters.character_details.truciciel import TrucicielCharacter

DB_CHARACTERS = {
    # # ====== MIESZKAŃCY ======
    "praczka": PraczkaCharacter(),
    "bibliotekarka": BibliotekarkaCharacter(),
    "detektyw": DetektywCharacter(),
    "kucharz": KucharzCharacter(),
    # "empata": EmpataCharacter(),
    # "jasnowidz": JasnowidzCharacter(),
    # "grabarz": GrabarzCharacter(),
    # "mnich": MnichCharacter(),
    # "krukarz": KrukarzCharacter(),
    # "dziewica": DziewicaCharacter(),
    # "zabojca": ZabojcaCharacter(),
    # "zolniez": ZolnierzCharacter(),
    # "burmistrz": BurmistrzCharacter(),
    # ====== OUTSIDER ======
    # "pijak": PijakCharacter(),
    # "swiety": SwietyCharacter(),
    # "lokaj": LokajCharacter(),
    # ====== MINIONKI ======
    "truciciel": TrucicielCharacter(),
    # "skarlet": SkarletCharacter(),
    # "baron": BaronCharacter(),
    # ====== DEMONY ======
    "imp": ImpCharacter(),
}


CHARACTERS_BY_TYPE = {
    "townsfolk": [
        char for char in DB_CHARACTERS.values() if char.role_type == RoleType.TOWNSFOLK
    ],
    "outsider": [
        char for char in DB_CHARACTERS.values() if char.role_type == RoleType.OUTSIDER
    ],
    "minion": [
        char for char in DB_CHARACTERS.values() if char.role_type == RoleType.MINION
    ],
    "demon": [
        char for char in DB_CHARACTERS.values() if char.role_type == RoleType.DEMON
    ],
}
