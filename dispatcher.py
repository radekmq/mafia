from queue import PriorityQueue

event_queue = PriorityQueue()
import threading

from flask_socketio import SocketIO

from game_events import Event
from logger import log_info
from player import PlayerVoteStatus
from utils import assign_random_characters, log_players_status_table


def get_log_players_status_event():
    return Event(
        name="log_players_status_table",
        actor_id="SYSTEM",
        priority=90,
    )


def update_state_view_for_all(priority=100):
    return Event(
        name="update_state_view_for_all",
        actor_id="SYSTEM",
        priority=priority,
    )


def update_state_view(player, data, priority=99):
    return Event(
        name="update_state_view",
        target=[player],
        actor_id="SYSTEM",
        priority=priority,
        data=data,
    )


class Dispatcher:
    def __init__(self, game_state, state_machine, game_setup, recluse_heuristic):
        self.event_queue = PriorityQueue()
        self.game_state = game_state
        self.state_machine = state_machine
        self.state_machine.register_dispatcher(self)
        self.game_setup = game_setup
        self.recluse_heuristic = recluse_heuristic
        self.socketio: SocketIO | None = None

    def register_socketio(self, socketio: SocketIO):
        """Inject SocketIO instance used for cross-thread emits."""
        self.socketio = socketio

    def worker(self):
        while True:
            priority, counter, event = event_queue.get()
            actor_name = (
                self.game_state.get_player_by_client_id(event.actor_id).name
                if event.actor_id != "SYSTEM"
                else "SYSTEM"
            )

            log_info("\n\n")
            log_info(
                f"- - - [DISPATCHER] Processing event: [{event.name}] with priority {priority} from actor {actor_name} - - -"
            )
            new_events = self.dispatch(event)
            log_info(f"[DISPATCHER] FINISHED PROCESSING EVENT: {event.name}")

            counter = 0
            for e in new_events:
                p = e.priority if hasattr(e, "priority") else 100
                event_queue.put((p, counter, e))
                counter += 1

            event_queue.task_done()

    def start_worker(self):
        log_info("Starting dispatcher worker thread.")
        thread = threading.Thread(target=self.worker, daemon=True)
        thread.start()

    def enqueue_event(self, event: Event):
        # Dodaje zdarzenie do kolejki z odpowiednim priorytetem
        priority = event.priority if hasattr(event, "priority") else 100
        counter = 0  # Można użyć licznika, aby zachować kolejność zdarzeń o tym samym priorytecie
        event_queue.put((priority, counter, event))

    def enqueue_events(self, events: list):
        # Dodaje zdarzenia do kolejki z odpowiednim priorytetem
        counter = 0  # Można użyć licznika, aby zachować kolejność zdarzeń o tym samym priorytecie
        for event in events:
            priority = event.priority if hasattr(event, "priority") else 100
            event_queue.put((priority, counter, event))
            counter += 1

    def dispatch(self, event: Event) -> list:
        # Implementacja logiki obsługi zdarzeń
        # Zwraca listę nowych zdarzeń do dodania do kolejki
        new_events = []

        if event.name == "next_game_state":
            self.state_machine.next_phase()

        elif event.name == "start_execution_phase":
            self.state_machine.start_execution_phase()

        elif event.name == "all_conditions_resolved":
            self.state_machine.all_conditions_resolved()

        elif event.name == "nominate_execute":
            current_player = self.game_state.get_player_by_client_id(event.actor_id)
            selected_player_id = (event.data or {}).get("selected_player")
            selected_player = self.game_state.get_player_by_client_id(
                selected_player_id
            )
            selected_player.set_nominated_for_execution(True)
            self.game_state.set_active_nominee_for_execution(selected_player)
            self.game_state.set_active_nominator(current_player)
            self.game_state.set_voting_order(current_player.seat_no)
            self.state_machine.next_phase()

        elif event.name == "vote_execute":
            current_player = self.game_state.get_player_by_client_id(event.actor_id)
            active_nominee = self.game_state.active_nominee_for_execution

            yes_no_vote = bool((event.data or {}).get("vote"))
            if yes_no_vote:
                active_nominee.increase_no_of_votes()
                current_player.set_vote_status(PlayerVoteStatus.VOTED_YES)
            else:
                current_player.set_vote_status(PlayerVoteStatus.VOTED_NO)

            new_event = Event(
                name="select_next_voter",
                actor_id="SYSTEM",
                priority=99,
            )
            new_events.append(new_event)
            voters_status = self.game_state.get_list_of_voters_and_statuses()
            for player in self.game_state.players:
                voting_data = {
                    "screen": "day_voting",
                    "voting_system": {
                        "screen_content": "idle_panel",
                        "voters_status": voters_status,
                    },
                }
                new_events.append(update_state_view(player, voting_data, 90))

        elif event.name == "enter_players_introduction":
            self.game_state.set_game_ongoing()
            self.game_state.sort_players_by_seat()
            self.game_state.reset_voting_statuses()
            assign_random_characters(self.game_state.players, self.game_setup)
            for player in self.game_state.players:
                priority = self.game_setup.effect_priorities.get(
                    "player_setup", {}
                ).get(player.character.name, 80)
                event = Event(
                    name="player_setup",
                    actor_id="SYSTEM",
                    target=[player],
                    priority=priority,
                )
                new_events.append(event)
                new_events.append(
                    update_state_view(
                        player,
                        {
                            "render_function": lambda player=player: player.character.render_page.introduction(
                                self, player
                            )
                        },
                    )
                )
            new_events.append(get_log_players_status_event())

        elif event.name == "player_setup":
            player = event.target[0]
            data = {
                "target": player,
                "game_state": self.game_state,
                "game_setup": self.game_setup,
            }
            player.character.ability.setup(data)

        elif event.name == "log_players_status_table":
            log_players_status_table(self.game_state)

        elif event.name == "enter_night_actions":
            self.game_state.reset_night_phase_variables()
            for player in self.game_state.players:
                # Reset night phase variables at the beginning of night phase
                event = Event(
                    name="reset_night_phase_variables",
                    actor_id="SYSTEM",
                    target=[player],
                    priority=0,
                )
                new_events.append(event)
                # Schedule night action events based on character abilities
                priority = self.game_setup.effect_priorities.get(
                    "night_actions", {}
                ).get(player.character.name, 90)
                event = Event(
                    name="player_night_action",
                    actor_id="SYSTEM",
                    target=[player],
                    priority=priority,
                )
                new_events.append(event)
                new_events.append(
                    update_state_view(
                        player,
                        {
                            "render_function": lambda player=player: player.character.render_page.night_action(
                                self, player
                            )
                        },
                    )
                )
            # Log status and broadcast state at the end of night actions scheduling
            new_events.append(get_log_players_status_event())

        elif event.name == "reset_night_phase_variables":
            player = event.target[0]
            player.reset_night_phase_variables()

        elif event.name == "player_night_action":
            player = event.target[0]
            data = {
                "target": player,
                "game_state": self.game_state,
                "game_setup": self.game_setup,
            }
            player.character.ability.night_action(
                data, is_fake=(player.drunk or player.poisoned)
            )

        elif event.name == "enter_night_resolution":
            for player in self.game_state.players:
                # Schedule night action events based on character abilities
                priority = self.game_setup.effect_priorities.get(
                    "night_resolution", {}
                ).get(player.character.name, 80)
                event = Event(
                    name="player_night_resolution",
                    actor_id="SYSTEM",
                    target=[player],
                    priority=priority,
                )
                new_events.append(event)
                new_events.append(
                    update_state_view(
                        player,
                        {
                            "render_function": lambda player=player: player.character.render_page.night_resolution(
                                self, player
                            )
                        },
                    )
                )
            # Log status and broadcast state at the end of night actions scheduling
            new_events.append(get_log_players_status_event())

        elif event.name == "player_night_resolution":
            player = event.target[0]
            data = {
                "target": player,
                "game_state": self.game_state,
                "game_setup": self.game_setup,
            }
            player.character.ability.night_resolution(
                data, is_fake=(player.drunk or player.poisoned)
            )

        elif event.name == "enter_game_score_calculation":
            self.recluse_heuristic.evaluate_game_advantage()
            new_event = Event(
                    name="game_score_calculated",
                    actor_id="SYSTEM",
                    priority=90,
                )
                new_events.append(new_event)

        elif event.name == "enter_day_discussions":
            for player in self.game_state.players:
                new_events.append(
                    update_state_view(player, {"screen": "day_discussion"})
                )

        elif event.name == "enter_day_nomination":
            alive_nomination_options = [
                {
                    "name": p.name,
                    "client_id": p.client_id,
                    "seat_no": p.seat_no,
                }
                for p in self.game_state.players
                if p.is_alive() and not p.is_nominated_for_execution()
            ]

            if not alive_nomination_options:
                log_info("No alive players available for nomination.")
                new_event = Event(
                    name="start_execution_phase",
                    actor_id="SYSTEM",
                    priority=99,
                )
                new_events.append(new_event)
                return new_events

            nominated_players = self.game_state.get_nominated_players_dict()
            for player in self.game_state.players:
                voting_data = {
                    "screen": "day_nomination",
                    "voting_system": {
                        "alive_nomination_options": alive_nomination_options,
                        "nominated_players": nominated_players,
                        "screen_content": "nomination_panel"
                        if player.is_alive()
                        else "status_panel",
                    },
                }
                new_events.append(update_state_view(player, voting_data))

        elif event.name == "enter_day_voting":
            voters_status = self.game_state.get_list_of_voters_and_statuses()
            log_info(f"Voters status for execution: {voters_status}")
            for player in self.game_state.players:
                voting_data = {
                    "screen": "day_voting",
                    "voting_system": {
                        "screen_content": "idle_panel",
                        "voters_status": voters_status,
                    },
                }
                new_events.append(update_state_view(player, voting_data, 90))
            new_event = Event(
                name="select_next_voter",
                actor_id="SYSTEM",
                priority=99,
            )
            new_events.append(new_event)

        elif event.name == "select_next_voter":
            voter = self.game_state.get_next_voter()
            log_info(f"Next voter for voting phase: {voter.name if voter else 'None'}")
            if voter is None:
                log_info("No voters available for voting phase.")
                for player in self.game_state.players:
                    player.reset_vote_status()
                self.game_state.reset_voting_index()
                self.state_machine.next_phase()
            else:
                log_info(
                    f"First voter for voting phase: {voter.name} (Seat {voter.seat_no})"
                )

                is_allowed_to_vote_yes = True
                if hasattr(voter.character, "can_vote_yes"):
                    log_info(
                        f"Checking if voter {voter.name} can vote YES based on their character ability."
                    )
                    is_allowed_to_vote_yes = voter.character.can_vote_yes(
                        voter, self.game_state
                    )
                else:
                    log_info(
                        f"Voter {voter.name} does not have a can_vote_yes ability; defaulting to allowed."
                    )

                voting_data = {
                    "screen": "day_voting",
                    "voting_system": {
                        "voter_id": voter.client_id if voter else None,
                        "voter_name": voter.name if voter else None,
                        "screen_content": "voting_panel",
                        "voters_status": self.game_state.get_list_of_voters_and_statuses(),
                        "active_nominee": self.game_state.active_nominee_for_execution.name
                        if self.game_state.active_nominee_for_execution
                        else None,
                        "allowed_to_vote_yes": is_allowed_to_vote_yes,
                    },
                }
                new_events.append(update_state_view(voter, voting_data))

        elif event.name == "enter_day_execution":
            player_winner = self.game_state.get_player_with_most_votes()
            if player_winner:
                player_winner.player_execution()
                self.game_state.set_last_executed_player(player_winner)
                execution_message = (
                    f"Miasto wyeliminowało gracza: {player_winner.name}."
                )
                log_info(
                    f"Player executed: {player_winner.name} (client_id: {player_winner.client_id})"
                )
            else:
                self.game_state.set_last_executed_player(None)
                execution_message = (
                    "Miasto nie wyeliminowało nikogo: remis lub brak głosów."
                )
                log_info("No player was executed due to a tie or no votes.")

            nominated_players = self.game_state.get_nominated_players_dict()
            log_info(f"Nominated players for execution: {nominated_players}")
            self.game_state.capture_last_day_voting_snapshot()
            self.game_state.reset_voting_statuses()
            for player in self.game_state.players:
                new_events.append(
                    update_state_view(
                        player,
                        {
                            "screen": "day_execution",
                            "voting_system": {
                                "nominated_players": nominated_players,
                                "execution_message": execution_message,
                            },
                        },
                    )
                )

        elif event.name == "player_connected":
            player = self.game_state.get_player_by_client_id(event.actor_id)
            log_info(">>> CONNECTED PLAYER: %s", player.name)
            player.set_socket_id(event.data["socket_id"])
            # Inform other players about the new connection
            new_events.append(update_state_view(player, player.active_screen))
            new_events.append(update_state_view_for_all())

        elif event.name == "leave_game":
            new_events.append(update_state_view_for_all())

        elif event.name == "update_state_view":
            player = event.target[0]
            if isinstance(event.data, dict) and "render_function" in event.data:
                player_data = event.data["render_function"]()
                player.set_active_screen(player_data)
            else:
                player.set_active_screen(event.data)
            data_view = self.game_state.data_view_for_endpoint(
                "state_update", player, self.state_machine.state
            )
            if self.socketio is None:
                log_info(
                    "SocketIO not registered in dispatcher; skipping state_update emit"
                )
                return new_events

            log_info(">>> SENDING STATE UPDATE TO PLAYER: %s", player.name)
            log_info(f"Update screen: {player.active_screen.get('screen', 'N/A')}")
            if player.active_screen.get("character_data") is not None:
                screen_content = player.active_screen.get("character_data", {}).get(
                    "screen_content", "N/A"
                )
                log_info(f"Update screen content: {screen_content}")
            self.socketio.emit("state_update", data_view, to=player.socket_id)

        elif event.name == "update_state_view_for_all":
            for player in self.game_state.players:
                data_view = self.game_state.data_view_for_endpoint(
                    "state_update", player, self.state_machine.state
                )
                if self.socketio is None:
                    log_info(
                        "SocketIO not registered in dispatcher; skipping state_update emit"
                    )
                    return new_events

                log_info(">>> SENDING STATE UPDATE TO PLAYER: %s", player.name)
                log_info(f"Update screen: {player.active_screen.get('screen', 'N/A')}")
                if player.active_screen.get("character_data") is not None:
                    screen_content = player.active_screen.get("character_data", {}).get(
                        "screen_content", "N/A"
                    )
                    log_info(f"Update screen content: {screen_content}")
                self.socketio.emit("state_update", data_view, to=player.socket_id)

        elif event.name == "imp_night_choice":
            player = self.game_state.get_player_by_client_id(event.actor_id)
            data = {
                "actor_id": event.actor_id,
                "game_state": self.game_state,
                "game_setup": self.game_setup,
                "callback_data": event.data,
            }
            screen_content = event.data.get("screen_content")
            if screen_content == "select_player_to_kill":
                events = player.character.ability.callback_imp_kills(data)
            elif screen_content == "select_replacement":
                events = player.character.ability.callback_suicide(data)
            if events:
                new_events.extend(events)

        elif event.name == "poisoner_night_choice":
            player = self.game_state.get_player_by_client_id(event.actor_id)
            data = {
                "actor_id": event.actor_id,
                "game_state": self.game_state,
                "game_setup": self.game_setup,
                "callback_data": event.data,
            }
            screen_content = event.data.get("screen_content")
            if screen_content == "select_player_to_poison":
                events = player.character.ability.callback_poison(data)
            if events:
                new_events.extend(events)

        elif event.name == "jasnowidz_night_choice":
            player = self.game_state.get_player_by_client_id(event.actor_id)
            data = {
                "target": player,
                "game_state": self.game_state,
                "game_setup": self.game_setup,
                "callback_data": event.data,
            }
            screen_content = event.data.get("screen_content")
            if screen_content == "select_player_to_see":
                events = player.character.ability.callback_i_see_you(data)
            if events:
                new_events.extend(events)

        elif event.name == "lokaj_night_choice":
            player = self.game_state.get_player_by_client_id(event.actor_id)
            data = {
                "actor": player,
                "game_state": self.game_state,
                "game_setup": self.game_setup,
                "callback_data": event.data,
            }
            screen_content = event.data.get("screen_content")
            if screen_content == "select_player":
                events = player.character.ability.callback_butler(data)
            if events:
                new_events.extend(events)

        elif event.name == "mnich_night_choice":
            player = self.game_state.get_player_by_client_id(event.actor_id)
            data = {
                "actor": player,
                "game_state": self.game_state,
                "game_setup": self.game_setup,
                "callback_data": event.data,
            }
            screen_content = event.data.get("screen_content")
            if screen_content == "select_player":
                events = player.character.ability.callback_mnich(data)
            if events:
                new_events.extend(events)

        elif event.name == "krukarz_night_choice":
            player = self.game_state.get_player_by_client_id(event.actor_id)
            data = {
                "actor": player,
                "game_state": self.game_state,
                "game_setup": self.game_setup,
                "callback_data": event.data,
            }
            screen_content = event.data.get("screen_content")
            if screen_content == "select_player":
                events = player.character.ability.callback_krukarz(data)
            if events:
                new_events.extend(events)

        elif event.name == "confirm_night_action":
            player = self.game_state.get_player_by_client_id(event.actor_id)
            player.confirm_night_action()
            new_events.append(
                update_state_view(
                    player,
                    {
                        "render_function": lambda: player.character.render_page.night_action(
                            self, player
                        )
                    },
                    priority=90,
                )
            )
            new_events.append(update_state_view_for_all())

        elif event.name == "imp_suicide_selected":
            player = self.game_state.get_player_by_client_id(event.actor_id)
            new_events.append(
                update_state_view(
                    player,
                    {
                        "render_function": lambda: player.character.render_page.demon_replacement(
                            self, player
                        )
                    },
                )
            )

        elif event.name == "enter_game_conditions_resolution":
            for player in self.game_state.players:
                if hasattr(player.character, "game_over_conditions"):
                    new_events.extend(
                        player.character.game_over_conditions(self.game_state)
                    )
            self.game_setup.game_over_conditions(self.game_state)
            event = Event(
                name="all_conditions_resolved",
                actor_id="SYSTEM",
                priority=50,
            )
            new_events.append(event)

        elif event.name == "enter_game_over":
            for player in self.game_state.players:
                new_events.append(update_state_view(player, {"screen": "game_over"}))

        elif event.name == "enter_lobby":
            for player in self.game_state.players:
                new_events.append(update_state_view(player, {"screen": "lobby"}))

        elif event.name == "exit_game_over":
            self.game_state.reset_game()

        return new_events
