"""Module for handling the state machine of the Mafia game."""

from flask import session, url_for
from transitions import Machine

from characters.character import RoleType
from game_state import GameState
from logger import log_info
from player import PlayerStatus
from state_machine_utils import assign_random_characters, log_players_status_table
from utils import EventIDGenerator, get_minion_action_status, log_dicts_table
from voting import VotingSystem
from characters.character_details.dead import DeadCharacter


class ClocktowerGame:
    """Handle the state machine for the Clocktower game."""

    def __init__(self):
        """Handle init."""
        # transitions.Machine nadpisuje ten atrybut podczas inicjalizacji FSM.
        self.state = "lobby"
        self.day_number = 0
        self.execution_count = 0
        self.game_state = GameState()
        self.voting_system = VotingSystem()

        # Wewnętrzna konfiguracja
        self._page_config = {}
        self._event_id_generator = EventIDGenerator()

    # =========================
    # HOOKI (ENTER)
    # =========================

    def on_enter_lobby(self):
        """Handle on enter lobby."""
        log_info("[SM on enter] Lobby – oczekiwanie na graczy")

    def on_enter_players_introduction(self):
        """Handle on enter players introduction."""
        log_info("[SM on enter] Przedstawienie ról graczy")
        self.game_state.game_ongoing = True
        self.game_state.players.sort(key=lambda p: p.seat_no) # sortowanie graczy według numeru miejsca
        assign_random_characters(self.game_state)
        for player in self.game_state.players:
            if player.character is not None:
                player.character.ability.setup(self, player)
        log_players_status_table(self.game_state)

    def on_enter_night_minion_action(self):
        """Handle on enter night minion action."""
        log_info("[SM on enter] Noc – akcje złych (Imp + miniony)")
        log_players_status_table(self.game_state)
        self.game_state.nominated_by_imp_to_die = None
        self.game_state.demon_replacement_candidate = None
        for player in self.game_state.players:
            player.poisoned = False

    def on_enter_night_all_players_action(self):
        """Handle on enter night all players action."""
        log_info("[SM on enter] Noc – akcje wszystkich postaci")
        log_players_status_table(self.game_state)

    def on_enter_night_summary(self):
        """Handle on enter night presentations."""
        log_info("[SM on enter] Noc – prezentacja ról i efektów nocnych")
        log_players_status_table(self.game_state)

    def on_enter_day_discussions(self):
        """Handle on enter day discussions."""
        self.day_number += 1
        log_info(f"[SM on enter] Dzień {self.day_number} – dyskusja")
        log_players_status_table(self.game_state)

    def on_enter_nomination(self):
        """Handle on enter nomination."""
        log_info("[SM on enter] Nominacje")

    def on_enter_voting(self):
        """Handle on enter voting."""
        log_info("[SM on enter] Głosowanie")

    def on_enter_execution(self):
        """Handle on enter execution."""
        self.execution_count += 1
        log_info(f"[SM on enter] Egzekucja nr {self.execution_count}")
        player_winner = self.voting_system.get_player_with_most_votes()
        if player_winner:
            winner_id = player_winner.client_id
            executed = self.game_state.get_player_by_client_id(winner_id)
            executed.alive = PlayerStatus.DEAD
            executed.character = DeadCharacter()
            log_info(f"Player executed: {executed.name} (client_id: {winner_id})")
            self.game_state.executed_player_name = (
                f"Tej nocy miasto wyeliminowało gracza: {executed.name}"
            )
        else:
            log_info("No player was executed due to a tie or no votes.")
            self.game_state.executed_player_name = (
                "Tej nocy miasto nie wyeliminowało nikogo."
            )
        self.voting_system.reset()

    def on_enter_game_over(self):
        """Handle on enter game over."""
        log_info("[SM on enter] KONIEC GRY")

    # =========================
    # HOOKI (EXIT)
    # =========================

    def on_exit_lobby(self):
        """Handle on exit lobby."""
        log_info("[SM on exit] Start gry")
        self.game_state.reset_game()

    def on_exit_players_introduction(self):
        """Handle on exit players introduction."""
        log_info("[SM on exit] Zakończono przedstawienie")

    def on_exit_night_minion_action(self):
        """Handle on exit night minion action."""
        log_info("[SM on exit] Minionki wykonały akcje")

    def on_exit_night_all_players_action(self):
        """Handle on exit night all players action."""
        log_info("[SM on exit] Wszystkie akcje nocne zakończone")
        for player in self.game_state.players:
            if player.character is not None:
                player.character.ability.on_night_exit(self, player)
                player.reset_admin_confirmation()
                player.reset_minion_confirmation()

    def on_exit_night_summary(self):
        """Handle on exit night presentations."""
        log_info("[SM on exit] Zakończono prezentacje nocne")

    def on_exit_day_discussions(self):
        """Handle on exit day discussions."""
        log_info("[SM on exit] Koniec dyskusji")

    def on_exit_nomination(self):
        """Handle on exit nomination."""
        log_info("[SM on exit] Koniec nominacji")

    def on_exit_voting(self):
        """Handle on exit voting."""
        log_info("[SM on exit] Koniec głosowania")
        self.voting_system.push_nominee_to_list()
        for player in self.game_state.players:
            player.reset_vote_status()

    def on_exit_execution(self):
        """Handle on exit execution."""
        log_info("[SM on exit] Zakończono egzekucję")

    # =========================
    # JEDYNY WARUNEK
    # =========================

    def should_end_game(self):
        """Zaimplementujesz: warunki zwycięstwa (Imp vs Town)."""

        log_info("[SM] Sprawdzanie warunków zakończenia gry")
        no_of_alive_players = len(
            [
                player
                for player in self.game_state.players
                if player.alive == PlayerStatus.ALIVE
            ]
        )
        log_info(f"Number of alive players: {no_of_alive_players}")
        is_demon_alive = any(
            player.alive == PlayerStatus.ALIVE
            and player.character is not None
            and player.character.role_type == RoleType.DEMON
            for player in self.game_state.players
        )
        log_info(f"Is Demon alive: {is_demon_alive}")

        # TEMP always false - DELETE when testing is done
        # return False
        return is_demon_alive is False or no_of_alive_players <= 2

    def page_configuration(self):
        """
        Page configuration.

        Funkcja śledzi zmiany w grze i aktualizuje konfigurację strony dla użytkowników.
        Jeśli stan gry zadeklarowany w page_config się zmieni, generuje nowe event_id,
        które może być używane do odświeżenia strony po stronie klienta.
        Dzięki temu klient może aktualizować interfejs użytkownika odpowiednio do aktualnego stanu.
        """

        active_voting_player_client_id = (
            self.voting_system.get_active_voter_client_id()
            if self.state == "voting"
            else None
        )
        player_vote_status = (
            [
                {"name": player.name, "vote_status": player.get_vote_status().value}
                for player in self.game_state.players
            ]
            if self.state == "voting"
            else None
        )

        admin_confirm_status = [
            {"name": player.name, "confirmed": player.is_admin_action_confirmed()}
            for player in self.game_state.players
        ]

        page_config = {
            "url": url_for(f"state_{self.state}"),
            "no_of_players": len(self.game_state.players),
            "active_voting_player_client_id": active_voting_player_client_id,
            "player_vote_status": player_vote_status,
            "admin_confirm_status": admin_confirm_status,
            "minion_action_status": get_minion_action_status(self),
        }

        if session.get("client_id") not in [
            player.client_id for player in self.game_state.players
        ]:
            log_info(
                "Unknown client accessing page configuration, redirecting to index."
            )
            page_config["url"] = url_for("index")

        previous_values = (
            {
                key: value
                for key, value in self._page_config.items()
                if key != "event_id"
            }
            if self._page_config
            else None
        )
        has_changed = not self._page_config or previous_values != page_config

        if has_changed:
            event_id = self._event_id_generator.next()
        else:
            event_id = self._page_config.get("event_id")

        page_config["event_id"] = event_id
        self._page_config.update(page_config)

        if has_changed:
            log_info(f"Page configuration: {page_config}")
            log_dicts_table(
                player_vote_status, title="Player vote status"
            ) if player_vote_status else None
            log_dicts_table(
                admin_confirm_status, title="Admin confirmation status"
            ) if admin_confirm_status else None

        return page_config


# =========================
# DEFINICJA FSM
# =========================

states = [
    "lobby",
    "players_introduction",
    "night_minion_action",
    "night_all_players_action",
    "night_summary",
    "day_discussions",
    "nomination",
    "voting",
    "execution",
    "game_over",
]

transitions = [
    # START
    {
        "trigger": "start_introduction",
        "source": "lobby",
        "dest": "players_introduction",
    },
    {
        "trigger": "start_evil_night_actions",
        "source": "players_introduction",
        "dest": "night_minion_action",
    },
    # NOC
    {
        "trigger": "start_all_players_night_actions",
        "source": "night_minion_action",
        "dest": "night_all_players_action",
    },
    {
        "trigger": "all_night_actions_done",
        "source": "night_all_players_action",
        "dest": "night_summary",
    },
    # 👉 PRIORYTET: najpierw sprawdzamy game_over
    {
        "trigger": "start_day_discussions",
        "source": "night_summary",
        "dest": "game_over",
        "conditions": "should_end_game",
    },
    {
        "trigger": "start_day_discussions",
        "source": "night_summary",
        "dest": "day_discussions",
    },
    # DZIEŃ
    {
        "trigger": "start_nomination_phase",
        "source": "day_discussions",
        "dest": "nomination",
    },
    {
        "trigger": "nomination_finished",
        "source": "nomination",
        "dest": "voting",
    },
    {
        "trigger": "voting_finished",
        "source": "voting",
        "dest": "nomination",
    },
    {
        "trigger": "start_execution_phase",
        "source": "nomination",
        "dest": "execution",
    },
    # 👉 ZNOWU: najpierw game_over
    {
        "trigger": "execution_finished",
        "source": "execution",
        "dest": "game_over",
        "conditions": "should_end_game",
    },
    {
        "trigger": "execution_finished",
        "source": "execution",
        "dest": "night_minion_action",
    },
    {
        "trigger": "finish_game",
        "source": "game_over",
        "dest": "lobby",
    },
]


# =========================
# INICJALIZACJA
# =========================

CLOCKTOWER_GAME = ClocktowerGame()

STATE_MACHINE = Machine(
    model=CLOCKTOWER_GAME,
    states=states,
    transitions=transitions,
    initial="lobby",
    auto_transitions=False,
)
