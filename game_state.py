"""Module for handling the game state and character definitions in the Mafia game."""


import threading
from uuid import uuid4

from flask import session

from logger import log_info
from player import Player
from utils import get_state_description


# pylint: disable=too-many-instance-attributes,too-many-arguments,too-many-positional-arguments
class GameState:
    """Class representing the game state."""

    def __init__(
        self,
        players: list[Player] | None = None,
        day: int = 0,
        action_truciciel_done: bool = False,
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
        self.action_truciciel_done = action_truciciel_done
        self.last_executed_player = None

        # ten atrybut określa, którego gracza Imp wybrał do zabicia w nocy.
        self.nominated_by_imp_to_die = None

        self.nominated_to_poison = None

        # określa kandydata do zastąpienia Demona
        self.demon_replacement_candidate = None

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
        self.execution_message = "Egzekucja nie została jeszcze rozstrzygnięta."

        self.lock = threading.Lock()
        self.active_user_rendered_state = "lobby"
        self.game_over_conditions_met = False
        self.active_nominee_for_execution = None
        self.active_nominator = None
        self.voting_index = 0
        self.voting_order = []
        self.winning_team = None
        self.last_day_voting_snapshot = []
        self.player_protected_by_mnich = None
        self.executed_by_virgin = None

    # =========================
    # FUNCTIONS OPERATING ON GAME STATE
    # =========================

    def if_player_exist(self, client_id: str) -> bool:
        """Check if player exists in database"""
        with self.lock:
            if client_id and any(
                player.client_id == client_id for player in self.players
            ):
                log_info(f"Player of {client_id=} already in game.")
                return True
        return False

    def if_seat_occupied(self, seat_no: int) -> bool:
        """Check if seat is occupied"""
        with self.lock:
            if seat_no in [player.seat_no for player in self.players]:
                log_info(f"Seat {seat_no=} is already occupied.")
                return True
        return False

    def if_name_already_exist(self, name: int) -> bool:
        """Check if seat is occupied"""
        with self.lock:
            if name in [player.name.lower() for player in self.players]:
                log_info(f"Name {name=} already exist in game.")
                return True
        return False

    def is_game_ongoing(self) -> bool:
        """Check if game is ongoing."""
        with self.lock:
            return self.game_ongoing

    def set_game_ongoing(self):
        """Set game ongoing."""
        with self.lock:
            self.game_ongoing = True

    def sort_players_by_seat(self):
        """Sort players by seat number."""
        with self.lock:
            self.players.sort(key=lambda p: p.seat_no)

    def get_player_by_client_id(self, client_id: str) -> Player | None:
        """Handle get player by client id."""
        with self.lock:
            for player in self.players:
                if player.client_id == client_id:
                    return player
        return None

    def get_player_name(self, client_id: str) -> str | None:
        """Handle get player name."""
        player = self.get_player_by_client_id(client_id)
        return player.name if player else None

    def reset_game(self):
        """Handle reset game."""
        with self.lock:
            self.day = 0
            self.action_truciciel_done = False
            self.last_executed_player = None
            self.nominated_by_imp_to_die = None
            self.kruk_died_last_night = False
            self.virgin_nomination_counter = 0
            self.alive_players_counter = 0
            self.alive_evil_players_counter = 0
            self.game_ongoing = False
            self.execution_message = "Egzekucja nie została jeszcze rozstrzygnięta."
            self.demon_replacement_candidate = None
            self.nominated_to_poison = None
            self.winning_team = None
            self.last_day_voting_snapshot = []
            self.game_over_conditions_met = False
            self.executed_by_virgin = None
            for player in self.players:
                player.reset_status()
            # Reset also the scenario setup (characters pool)
            if hasattr(self, "game_setup") and self.game_setup is not None:
                self.game_setup.reset_setup()

    def add_new_player(self, name, seat_no, moderator=False, password=None):
        is_admin = False
        if moderator:  # and password == "secret":
            is_admin = True

        client_id = str(uuid4())
        session["client_id"] = client_id

        player = Player(
            client_id=client_id, seat_no=seat_no, name=name, is_admin=is_admin
        )

        with self.lock:
            self.players.append(player)
        log_info(
            f"Saved player: {name}, seat: {seat_no}, moderator: {'TAK' if is_admin else 'NIE'}"
        )

    def remove_player(self, client_id):
        if client_id:
            with self.lock:
                self.players = [
                    player for player in self.players if player.client_id != client_id
                ]
            log_info(f"Player left the game: {client_id}")

    def set_demon_replacement_candidate(self, player: Player | None):
        """Set demon replacement candidate."""
        log_info(
            f"Setting demon replacement candidate: {player.name if player else 'None'}"
        )
        with self.lock:
            self.demon_replacement_candidate = player

    def set_nominated_by_imp_to_die(self, player: str | None):
        """Set nominated by imp to die."""
        player = self.get_player_by_client_id(player) if player else None
        log_info(
            f"Setting nominated by Imp to die: {player.name if player else 'None'}"
        )
        with self.lock:
            self.nominated_by_imp_to_die = player

    def set_nominated_to_poison(self, player: str | None):
        """Set nominated to poison."""
        player = self.get_player_by_client_id(player) if player else None
        log_info(f"Setting nominated to poison: {player.name if player else 'None'}")
        with self.lock:
            self.nominated_to_poison = player

    def reset_night_phase_variables(self):
        """Reset night phase variables."""
        with self.lock:
            self.demon_replacement_candidate = None
            self.nominated_by_imp_to_die = None
            self.nominated_to_poison = None

    def data_view_for_endpoint(self, endpoint: str, player: Player, state) -> dict:
        """Get data view for endpoint."""
        with self.lock:
            players_alive_status = [
                {
                    "name": f"{p.name} (pozycja: {p.seat_no})",
                    "alive": p.is_alive(),
                }
                for p in self.players
            ]
            players_night_action = [
                {
                    "name": p.name,
                    "status": "Tak" if p.is_night_action_done() else "Nie",
                }
                for p in self.players
                if p.is_alive()
            ]
            data_view = {
                "state_update": {
                    "phase": state,
                    "screen": player.active_screen.get("screen", "lobby")
                    if isinstance(player.active_screen, dict)
                    else "lobby",
                    "player_client_id": player.client_id,
                    "player_name": player.name,
                    "player_seat": player.seat_no,
                    "players_alive_status": players_alive_status,
                    "is_alive": player.is_alive(),
                    "game_state_description": get_state_description(state),
                    "is_admin": player.is_administrator(),
                    "players_night_action_status": players_night_action,
                    "player_confirmed_action": player.is_night_action_done(),
                    "character_data": player.active_screen.get("character_data", {})
                    if isinstance(player.active_screen, dict)
                    else {},
                    "voting_system": player.active_screen.get("voting_system", {})
                    if isinstance(player.active_screen, dict)
                    else {},
                    "winning_team": self.winning_team,
                },
            }

            if endpoint in data_view.keys():
                return data_view[endpoint]
            else:
                log_info(f"No data view found for endpoint: {endpoint}")
                return {}

    def set_active_nominee_for_execution(self, player: Player | None):
        """Set active nominee for execution."""
        log_info(
            f"Setting active nominee for execution: {player.name if player else 'None'}"
        )
        with self.lock:
            self.active_nominee_for_execution = player

    def get_active_nominee_for_execution(self) -> Player | None:
        """Get active nominee for execution."""
        with self.lock:
            return self.active_nominee_for_execution

    def set_active_nominator(self, player: Player | None):
        """Set active nominator."""
        log_info(f"Setting active nominator: {player.name if player else 'None'}")
        with self.lock:
            self.active_nominator = player

    def get_active_nominator(self) -> Player | None:
        """Get active nominator."""
        with self.lock:
            return self.active_nominator

    def increment_voting_index(self):
        """Increment voting index."""
        with self.lock:
            self.voting_index += 1

    def get_voting_index(self) -> int:
        """Get voting index."""
        with self.lock:
            return self.voting_index

    def reset_voting_index(self):
        """Reset voting index."""
        with self.lock:
            self.voting_index = 0

    def sort_players_from_seat(self, start_seat):
        return sorted(
            self.players, key=lambda p: (p.seat_no - start_seat) % len(self.players)
        )

    def set_voting_order(self, seat_no):
        """Set voting order based on nominator's seat number."""
        with self.lock:
            sorted_players = self.sort_players_from_seat(seat_no)
            self.voting_order = [
                p for p in sorted_players if p.is_alive() or p.has_last_vote()
            ]
            log_info(
                f"Voting order set based on nominator's seat {seat_no}: {[p.name for p in self.voting_order]}"
            )

    def get_next_voter(self):
        """Get next voter."""
        if not self.active_nominee_for_execution or not self.active_nominator:
            return None

        voting_index = self.get_voting_index()
        log_info(f"Current voting index: {voting_index}")

        if not self.voting_order:
            log_info("No players allowed to vote.")
            return None
        if voting_index >= len(self.voting_order):
            log_info("Voting index exceeds number of allowed voters.")
            return None

        next_voter = self.voting_order[voting_index]
        self.increment_voting_index()
        log_info(f"Next voter is: {next_voter.name} (Seat {next_voter.seat_no})")
        return next_voter

    def get_player_with_most_votes(self) -> Player | None:
        """Get player with most votes."""
        with self.lock:
            nominated_players = [
                p for p in self.players if p.is_nominated_for_execution()
            ]
            if not nominated_players:
                log_info("No nominated players to vote for.")
                return None

            max_votes = max(p.number_of_votes for p in nominated_players)
            if max_votes == 0:
                log_info("No votes cast for any nominated player.")
                return None
            players_with_max_votes = [
                p for p in nominated_players if p.number_of_votes == max_votes
            ]

            if len(players_with_max_votes) == 1:
                log_info(
                    f"Player with most votes: {players_with_max_votes[0].name} with {max_votes} votes."
                )
                return players_with_max_votes[0]
            else:
                log_info(
                    f"Tie between players: {[p.name for p in players_with_max_votes]} with {max_votes} votes each."
                )
                return None

    def set_last_executed_player(self, player: Player | None):
        """Set last executed player."""
        log_info(f"Setting last executed player: {player.name if player else 'None'}")
        with self.lock:
            self.last_executed_player = player

    def get_nominated_players_dict(self) -> list[dict]:
        """Get nominated players."""
        with self.lock:
            nominated_players = [
                p for p in self.players if p.is_nominated_for_execution()
            ]
            if not nominated_players:
                log_info("No nominated players to vote for.")
                return []
            return [
                {"name": p.name, "votes": p.number_of_votes} for p in nominated_players
            ]

    def get_nominated_players(self) -> list:
        """Get nominated players."""
        with self.lock:
            nominated_players = [
                p for p in self.players if p.is_nominated_for_execution()
            ]
            if not nominated_players:
                log_info("No nominated players to vote for.")
                return []
            return nominated_players

    def reset_voting_statuses(self):
        """Reset voting statuses for all players."""
        self.set_active_nominee_for_execution(None)
        self.set_active_nominator(None)
        for player in self.players:
            player.set_nominated_for_execution(False)
            player.reset_no_of_votes()

    def capture_last_day_voting_snapshot(self):
        """Capture nominated players and vote counts before they are reset."""
        with self.lock:
            nominated_players = [
                p for p in self.players if p.is_nominated_for_execution()
            ]
            self.last_day_voting_snapshot = [
                {
                    "name": p.name,
                    "character_name": p.character.name,
                    "role_type": p.character.role_type,
                    "votes": p.number_of_votes,
                }
                for p in nominated_players
            ]

    def get_last_day_voting_snapshot(self) -> list[dict]:
        """Return a copy of the last captured day voting snapshot."""
        with self.lock:
            return list(self.last_day_voting_snapshot)

    def get_list_of_voters_and_statuses(self) -> list[dict]:
        """Get list of voters and their statuses."""
        return [
            {"name": p.name, "status": p.get_vote_status().value} for p in self.players
        ]

    def set_game_over_conditions_met(self, value: bool):
        """Set game over conditions met."""
        log_info(f"Setting game over conditions met: {value}")
        with self.lock:
            self.game_over_conditions_met = value

    def set_player_protected_by_mnich(self, player: Player | None):
        """Set player protected by Mnich."""
        log_info(
            f"Setting player protected by Mnich: {player.name if player else 'None'}"
        )
        with self.lock:
            self.player_protected_by_mnich = player

    def reset_player_protected_by_mnich(self):
        """Reset player protected by Mnich."""
        log_info("Resetting player protected by Mnich.")
        if self.player_protected_by_mnich:
            self.player_protected_by_mnich.set_protected(False)
        with self.lock:
            self.player_protected_by_mnich = None

    def get_player_protected_by_mnich(self) -> Player | None:
        """Get player protected by Mnich."""
        with self.lock:
            return self.player_protected_by_mnich

    def increment_day(self):
        """Increment day counter."""
        with self.lock:
            self.day += 1

    def set_executed_by_virgin(self, player: Player | None):
        """Set executed by Virgin."""
        log_info(f"Setting executed by Virgin: {player.name if player else 'None'}")
        with self.lock:
            self.executed_by_virgin = player

    def reset_executed_by_virgin(self):
        """Reset executed by Virgin."""
        log_info("Resetting executed by Virgin.")
        with self.lock:
            self.executed_by_virgin = None

    def get_executed_by_virgin(self) -> Player | None:
        """Get executed by Virgin."""
        with self.lock:
            return self.executed_by_virgin
