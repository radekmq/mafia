"""Module for handling the game state and character definitions in the Mafia game."""


from flask import session

from player import Player


# pylint: disable=too-many-instance-attributes,too-many-arguments,too-many-positional-arguments
class GameState:
    """Class representing the game state."""

    def __init__(
        self,
        players: list[Player] | None = None,
        day: int = 0,
        night: int = 0,
        action_truciciel_done: bool = False,
        action_imp_done: bool = False,
        last_executed_player: Player | None = None,
        nominated_by_imp_to_die: Player | None = None,
        demon_replacement_candidate: Player | None = None,
        kruk_died_last_night: bool = False,
        virgin_nomination_counter: int = 0,
        auto_game: bool = False,
        alive_players_counter: int = 0,
        alive_evil_players_counter: int = 0,
        execute_on_majority: bool = False,
        game_ongoing: bool = False,
    ):
        """Handle init."""
        self.players = players or []
        self.day = day
        self.night = night
        self.action_truciciel_done = action_truciciel_done
        self.action_imp_done = action_imp_done
        self.last_executed_player = last_executed_player

        # ten atrybut określa, którego gracza Imp wybrał do zabicia w nocy.
        self.nominated_by_imp_to_die = nominated_by_imp_to_die

        # określa kandydata do zastąpienia Demona
        self.demon_replacement_candidate = demon_replacement_candidate

        # określa czy kruk zginął poprzedniej nocy
        self.kruk_died_last_night = kruk_died_last_night

        # licznik nominacji dziewiczej, potrzebny do sprawdzania warunku zwycięstwa Mieszkańców
        self.virgin_nomination_counter = virgin_nomination_counter

        # jeśli True, to gra będzie przebiegać automatycznie, z minimalną interakcją moderatora
        self.auto_game = auto_game

        # ten licznik jest potrzebny do sprawdzania warunku zwycięstwa Mieszkańców
        self.alive_players_counter = alive_players_counter

        # ten licznik jest potrzebny do sprawdzania warunku zwycięstwa Minionów i Demona
        self.alive_evil_players_counter = alive_evil_players_counter

        # jeśli True, to egzekucja w ciągu dnia nastąpi po bezwzględnej większości głosów
        self.execute_on_majority = execute_on_majority

        # czy gra jest w toku, czy zakończyła się zwycięstwem którejś ze stron
        self.game_ongoing = game_ongoing

    # =========================
    # FUNCTIONS OPERATING ON GAME STATE
    # =========================

    def get_current_player(self) -> Player | None:
        """Get the current player based on the session's client_id."""
        # This function assumes that there is a session management system in place
        # that assigns a unique client_id to each player. The actual implementation
        # of session management is not shown here.
        client_id = session.get("client_id")
        return self.get_player_by_client_id(client_id)

    def get_player_by_client_id(self, client_id: str) -> Player | None:
        """Handle get player by client id."""
        for player in self.players:
            if player.client_id == client_id:
                return player
        return None

    def get_player_by_character_name(self, character_name: str) -> Player | None:
        """Handle get player by character name."""
        for player in self.players:
            if player.character and player.character.name == character_name:
                return player
        return None

    def get_player_name(self, client_id: str) -> str | None:
        """Handle get player name."""
        player = self.get_player_by_client_id(client_id)
        return player.name if player else None

    def reset_game(self):
        """Handle reset game."""
        self.day = 0
        self.night = 0
        self.action_truciciel_done = False
        self.action_imp_done = False
        self.last_executed_player = None
        self.nominated_by_imp_to_die = None
        self.kruk_died_last_night = False
        self.virgin_nomination_counter = 0
        self.alive_players_counter = 0
        self.alive_evil_players_counter = 0
        self.demon_replacement_candidate = None
        for player in self.players:
            player.reset_status()
