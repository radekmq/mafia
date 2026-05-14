"""Module for handling the game state and character definitions in the Mafia game."""


from characters.character import RoleType
from characters.character_details.empata import EmpataCharacter
from characters.character_details.grabarz import GrabarzCharacter
from characters.character_details.imp import ImpCharacter
from characters.character_details.jasnowidz import JasnowidzCharacter
from characters.character_details.krukarz import KrukarzCharacter
from characters.character_details.mnich import MnichCharacter
from characters.character_details.pustelnik import PustelnikCharacter
from characters.character_details.skarlet import SkarletCharacter
from characters.character_details.zolnierz import ZolnierzCharacter
from characters.scenario import Scenario
from logger import log_info
from player import PlayerStatus


class TroubleBrewingScenario(Scenario):
    """Scenario for Trouble Brewing setup."""

    def __init__(self):
        super().__init__()

        # ====== MIESZKAŃCY ======
        # self.add_character(PraczkaCharacter())
        # self.add_character(BibliotekarkaCharacter())
        # self.add_character(DetektywCharacter())
        # self.add_character(KucharzCharacter())
        self.add_character(EmpataCharacter())
        self.add_character(JasnowidzCharacter())
        self.add_character(GrabarzCharacter())
        self.add_character(ZolnierzCharacter())
        self.add_character(MnichCharacter())
        self.add_character(KrukarzCharacter())

        # ====== OUTSIDER ======
        # self.add_character(PijakCharacter())
        # self.add_character(SwietyCharacter())
        # self.add_character(LokajCharacter())
        self.add_character(PustelnikCharacter())

        # ====== MINIONKI ======
        # self.add_character(TrucicielCharacter())
        self.add_character(SkarletCharacter())

        # ====== DEMONY ======
        self.add_character(ImpCharacter())

        self.trouble_brewing_setup = [
            # To be deleted
            {
                "liczba_graczy": 1,
                "Mieszkańcy": 0,
                "Outsiderzy": 1,
                "Minionki": 0,
                "Demon": 0,
            },
            {
                "liczba_graczy": 2,
                "Mieszkańcy": 2,
                "Outsiderzy": 0,
                "Minionki": 0,
                "Demon": 0,
            },
            {
                "liczba_graczy": 3,
                "Mieszkańcy": 0,
                "Outsiderzy": 1,
                "Minionki": 1,
                "Demon": 1,
            },
            {
                "liczba_graczy": 4,
                "Mieszkańcy": 1,
                "Outsiderzy": 1,
                "Minionki": 1,
                "Demon": 1,
            },
            # Up to here
            {
                "liczba_graczy": 5,
                "Mieszkańcy": 3,
                "Outsiderzy": 0,
                "Minionki": 1,
                "Demon": 1,
            },
            {
                "liczba_graczy": 6,
                "Mieszkańcy": 3,
                "Outsiderzy": 1,
                "Minionki": 1,
                "Demon": 1,
            },
            {
                "liczba_graczy": 7,
                "Mieszkańcy": 5,
                "Outsiderzy": 0,
                "Minionki": 1,
                "Demon": 1,
            },
            {
                "liczba_graczy": 8,
                "Mieszkańcy": 5,
                "Outsiderzy": 1,
                "Minionki": 1,
                "Demon": 1,
            },
            {
                "liczba_graczy": 9,
                "Mieszkańcy": 5,
                "Outsiderzy": 2,
                "Minionki": 1,
                "Demon": 1,
            },
            {
                "liczba_graczy": 10,
                "Mieszkańcy": 7,
                "Outsiderzy": 0,
                "Minionki": 2,
                "Demon": 1,
            },
            {
                "liczba_graczy": 11,
                "Mieszkańcy": 7,
                "Outsiderzy": 1,
                "Minionki": 2,
                "Demon": 1,
            },
            {
                "liczba_graczy": 12,
                "Mieszkańcy": 7,
                "Outsiderzy": 2,
                "Minionki": 2,
                "Demon": 1,
            },
            {
                "liczba_graczy": 13,
                "Mieszkańcy": 9,
                "Outsiderzy": 0,
                "Minionki": 3,
                "Demon": 1,
            },
            {
                "liczba_graczy": 14,
                "Mieszkańcy": 9,
                "Outsiderzy": 1,
                "Minionki": 3,
                "Demon": 1,
            },
            {
                "liczba_graczy": 15,
                "Mieszkańcy": 9,
                "Outsiderzy": 2,
                "Minionki": 3,
                "Demon": 1,
            },
        ]

        self.effect_priorities = {
            "player_setup": {
                # default: 80
                "Baron": 10,
            },
            "night_actions": {},
            "night_resolution": {
                # default: 80
                "Truciciel": 10,
                "Imp": 90,
                "Krukarz": 95,
            },
        }

        self.character_power = {
            # Townsfolk
            "Praczka": 2,
            "Bibliotekarka": 2,
            "Detektyw": 2,
            "Kucharz": 3,
            "Empata": 4,
            "Jasnowidz": 5,
            "Grabarz": 5,
            "Mnich": 3,
            "Krukarz": 3,
            "Dziewica": 4,
            "Zabojca": 3,
            "Żołnierz": 2,
            "Burmistrz": 4,
            # Outsiders
            "Lokaj": -1,
            "Pijak": -4,
            "Święty": -5,
            # Minions
            "Truciciel": -5,
            "Skarlet": -4,
            "Baron": -4,
            # Demon
            "Imp": -6,
        }

    def game_over_conditions(self, game_state) -> bool:
        """Check game over conditions."""
        log_info("Checking game over conditions for Trouble Brewing scenario.")

        no_of_alive_players = len(
            [
                player
                for player in game_state.players
                if player.alive == PlayerStatus.ALIVE
            ]
        )
        log_info(f"Number of alive players: {no_of_alive_players}")
        is_demon_alive = any(
            player.alive == PlayerStatus.ALIVE
            and player.character is not None
            and player.character.role_type == RoleType.DEMON
            for player in game_state.players
        )
        is_any_good_alive = any(
            player.alive == PlayerStatus.ALIVE
            and player.character is not None
            and player.character.role_type in [RoleType.TOWNSFOLK, RoleType.OUTSIDER]
            for player in game_state.players
        )
        log_info(f"Is Demon alive: {is_demon_alive}")
        log_info(f"Is any good alive: {is_any_good_alive}")

        if is_demon_alive is False:
            log_info("Game over condition met: Good wins the game.")
            game_state.winning_team = "Dobrzy (Mieszczanie + Outsiderzy)"
            game_state.set_game_over_conditions_met(True)
        elif no_of_alive_players <= 2:
            log_info("Game over condition met: Evil wins the game.")
            game_state.winning_team = "Źli (Minionki + Demon)"
            game_state.set_game_over_conditions_met(True)
        elif is_any_good_alive is False:
            log_info("Game over condition met: Evil wins the game.")
            game_state.winning_team = "Źli (Minionki + Demon)"
            game_state.set_game_over_conditions_met(True)
        else:
            log_info("Game over conditions not fullfilled!")

        return []
