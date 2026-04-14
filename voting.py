"""Module for handling the player definitions in the Mafia game."""

import threading
from dataclasses import dataclass

from logger import log_info
from player import Player, PlayerStatus


@dataclass
class NominatedPlayer:
    client_id: str
    votes: int = 0
    name: str = ""

    def to_dict(self) -> dict:
        return {"votes": self.votes, "name": self.name}


# pylint: disable=too-many-instance-attributes,too-many-arguments,too-many-positional-arguments
class VotingSystem:
    """Class representing the voting system."""

    def __init__(self):
        """Handle init."""
        self.active_voter_index = None
        self.nominated_players = []
        self.active_nominee_player = None
        self.list_of_players_with_last_vote = []
        self.list_of_nominee_voters = []
        self.lock = threading.Lock()
        self.vote_right_players = []

    def reset(self):
        """Handle reset status."""
        with self.lock:
            self.active_voter_index = None
            self.nominated_players = []
            self.active_nominee_player = None
            self.list_of_players_with_last_vote = []
            self.list_of_nominee_voters = []
            self.players_with_rigth_to_vote = []

    def get_active_voter_client_id(self) -> str:
        """Get active voter client id."""
        with self.lock:
            return (
                self.players_with_rigth_to_vote[self.active_voter_index].client_id
                if self.active_voter_index is not None
                else None
            )

    def set_nominator(self, nominator: Player, players: list[Player]):
        """Set active nominator client id."""
        with self.lock:
            self.players_with_rigth_to_vote = [
                player
                for player in players
                if player.alive == PlayerStatus.ALIVE
                or (player.client_id in self.list_of_players_with_last_vote)
            ]

            if len(self.players_with_rigth_to_vote) > 1:
                start_index = next(
                    i
                    for i, el in enumerate(self.players_with_rigth_to_vote)
                    if el.client_id == nominator.client_id
                )
                self.players_with_rigth_to_vote = (
                    self.players_with_rigth_to_vote[start_index:]
                    + self.players_with_rigth_to_vote[:start_index]
                )
            self.active_voter_index = 0
            log_info(
                f"Voting order set. Players with right to vote: {[player.name for player in self.players_with_rigth_to_vote]}, starting with nominator: {nominator.name}"
            )

    def get_nominated_players(self) -> list[NominatedPlayer]:
        """Get nominated players."""
        with self.lock:
            return self.nominated_players

    def get_nominated_players_json(self) -> list[dict]:
        """Get nominated players as JSON."""
        with self.lock:
            return [player.to_dict() for player in self.nominated_players]

    def append_nominated_player(self, player: Player):
        """Append nominated player."""
        with self.lock:
            if self.active_nominee_player is not None:
                self.nominated_players.append(self.active_nominee_player)

            nominee_names = [
                player.name if player is not None else "None"
                for player in self.nominated_players
            ]
            log_info(f"Nominated players: {nominee_names}")
            self.active_nominee_player = NominatedPlayer(
                client_id=player.client_id, name=player.name
            )

    def vote_for_active_nominee(self, player: Player):
        """Vote for active nominee by player."""
        if player.alive == PlayerStatus.ALIVE:
            log_info("Current player is alive during voting, process vote.")
            if self.active_nominee_player is not None:
                self.active_nominee_player.votes += 1
                self.list_of_nominee_voters.append(player.client_id)

        else:
            log_info("Current player is dead during voting.")
            if player.client_id in self.list_of_players_with_last_vote:
                if self.active_nominee_player is not None:
                    self.active_nominee_player.votes += 1
                    self.list_of_players_with_last_vote.remove(player.client_id)
                    self.list_of_nominee_voters.append(player.client_id)

    def push_nominee_to_list(self):
        """Push nominee to list."""
        with self.lock:
            if self.active_nominee_player is not None:
                self.nominated_players.append(self.active_nominee_player)
                self.active_nominee_player = None
                nominee_names = [
                    player.name if player is not None else "None"
                    for player in self.nominated_players
                ]
                log_info(f"Nominated players: {nominee_names}")
                self.nominated_players.sort(key=lambda x: x.votes, reverse=True)
            self.list_of_nominee_voters = []
            self.active_voter_index = None

    def get_player_with_most_votes(self) -> NominatedPlayer | None:
        """Get player with most votes."""
        with self.lock:
            if not self.nominated_players:
                return None

            highest_votes = max(player.votes for player in self.nominated_players)
            players_with_highest_votes = [
                player
                for player in self.nominated_players
                if player.votes == highest_votes
            ]

            if len(players_with_highest_votes) != 1:
                return None

            return players_with_highest_votes[0]

    def is_vote_submitted(self, client_id: str) -> bool:
        """Check if vote is submitted by client id."""
        with self.lock:
            return client_id in self.list_of_nominee_voters

    def apply_next_voter(self) -> bool:
        """Get next voter client id."""
        with self.lock:
            self.active_voter_index += 1
            if self.active_voter_index >= len(self.players_with_rigth_to_vote):
                self.active_voter_index = 0
                return False  # Oznacza, że wszyscy głosujący oddali już swój głos
            return True

    def is_player_nominated(self, client_id: str) -> bool:
        """Check if player is nominated by client id."""
        with self.lock:
            return any(
                player.client_id == client_id for player in self.nominated_players
            ) or (
                self.active_nominee_player
                and self.active_nominee_player.client_id == client_id
            )

    def is_player_in_voting_list(self, client_id: str) -> bool:
        """Check if player is in voting list by client id."""
        with self.lock:
            return any(
                player.client_id == client_id
                for player in self.players_with_rigth_to_vote
            )
