# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
from flask_socketio import SocketIO, join_room, leave_room, emit
from uuid import uuid4
from utils import Database, assign_players_to_characters, fun_praczka, test_enabled
import random
import inspect

from database import db_characters, trouble_brewing_setup
import time

app = Flask(__name__)
app.secret_key = "tajny_klucz"
socketio = SocketIO(app, cors_allowed_origins="*")

# ======= STAN GRY =======
clients = {}
db_players = Database()
db_game = {
    "game_active": False,
    "char_presented": False,
    "mode": "day",
    "day_number": 1,
    "no_of_players": 0,
    "admin_id": None,
    "players": [],
    "winner": None,
    "nominator_last_day": {},
    "imp_action_done_night": False,
    "truciciel_action_done_night": False,
}
db_game_selection = None

DEFAULT_TEST_PLAYERS = [
    {
        "client_id": f"default-test-player-{index}",
        "name": f"Test gracz {index}",
        "seat": index,
        "executed": False,
        "vote_dead": True,
    }
    for index in range(1, 6)
]

execution_vote_state = {
    "active": False,
    "vote_id": 0,
    "nominator_client_id": None,
    "nominator_name": None,
    "nominator_seat": None,
    "nominee_client_id": None,
    "nominee_name": None,
    "votes": {},
    "required_voters": [],
    "optional_voters": [],
    "last_result": None,
}

ALLOWED_BACK_ENDPOINTS = {"lobby", "handle_menu", "index", "player_page"}


def parse_seat(raw_seat):
    if raw_seat is None or str(raw_seat).strip() == "":
        raise ValueError("Numer miejsca jest wymagany")

    try:
        seat = int(str(raw_seat).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError("Numer miejsca musi być liczbą całkowitą") from exc

    if seat < 1:
        raise ValueError("Numer miejsca musi być większy od zera")

    return seat


def ensure_player_flags(player):
    player.setdefault("executed", False)
    player.setdefault("vote_dead", True)


def get_alive_player_ids():
    alive_players = []
    for client_id, player in db_players.get_all().items():
        ensure_player_flags(player)
        if not player["executed"]:
            alive_players.append(client_id)
    return alive_players


def get_optional_dead_voter_ids():
    optional_voters = []
    for client_id, player in db_players.get_all().items():
        ensure_player_flags(player)
        if player["executed"] and player["vote_dead"]:
            optional_voters.append(client_id)
    return optional_voters


def build_nomination_candidates_payload(client_id):
    if not client_id or client_id not in db_players:
        return {"error": "Nie znaleziono gracza."}

    ensure_player_flags(db_players[client_id])
    if db_players[client_id]["executed"]:
        return {"error": "Gracz wyeliminowany nie może nominować."}

    if execution_vote_state["active"]:
        return {"error": "Trwa już inne głosowanie."}

    candidates = []
    for candidate_id in get_alive_player_ids():
        player = db_players[candidate_id]
        candidates.append(
            {
                "client_id": candidate_id,
                "name": player.get("name", "Nieznany"),
                "seat": player.get("seat"),
            }
        )

    return {"players": candidates}


def get_sorted_player_options():
    players = []
    for listed_client_id, player in sorted(
        db_players.get_all().items(),
        key=lambda item: item[1].get("seat") or 9999,
    ):
        ensure_player_flags(player)
        players.append(
            {
                "client_id": listed_client_id,
                "name": player.get("name", "Nieznany"),
                "seat": player.get("seat"),
                "executed": player.get("executed", False),
            }
        )
    return players


def redirect_players_to_endpoint(endpoint_name, target_client_ids=None, **values):
    target_client_ids = list(target_client_ids or db_players.get_all_client_ids())
    target_url = url_for(endpoint_name, **values)

    for client_id in target_client_ids:
        if client_id not in db_players:
            continue

        player = db_players[client_id]

        sid = player.get("sid")
        if not sid:
            continue

        socketio.emit("redirect_user", {"url": target_url}, to=sid)

    socketio.emit(
        "redirect_user_for_clients",
        {"url": target_url, "target_client_ids": target_client_ids},
    )


def build_execution_vote_page_context(client_id):
    if not execution_vote_state["active"]:
        return None

    ensure_player_flags(db_players[client_id])

    required_voters = set(execution_vote_state["required_voters"])
    optional_voters = set(execution_vote_state["optional_voters"])
    current_votes = execution_vote_state["votes"]

    return {
        "vote_id": execution_vote_state.get("vote_id", 0),
        "nominator_name": execution_vote_state.get("nominator_name") or "Nieznany",
        "nominator_seat": execution_vote_state.get("nominator_seat"),
        "nominee_name": execution_vote_state["nominee_name"],
        "nominee_client_id": execution_vote_state["nominee_client_id"],
        "can_vote": (
            client_id in required_voters or client_id in optional_voters
        ) and client_id not in current_votes,
        "has_voted": client_id in current_votes,
        "required_votes_cast": sum(1 for voter in current_votes if voter in required_voters),
        "required_votes_total": len(required_voters),
        "yes_votes": sum(1 for vote in current_votes.values() if vote == "yes"),
        "no_votes": sum(1 for vote in current_votes.values() if vote == "no"),
    }


def build_execution_vote_public_status():
    if not execution_vote_state["active"]:
        return {
            "active": False,
            "last_result": execution_vote_state.get("last_result"),
            "server_ts": int(time.time() * 1000),
        }

    required_voters = set(execution_vote_state["required_voters"])
    current_votes = execution_vote_state["votes"]

    return {
        "active": True,
        "vote_id": execution_vote_state.get("vote_id", 0),
        "nominator_name": execution_vote_state.get("nominator_name") or "Nieznany",
        "nominator_seat": execution_vote_state.get("nominator_seat"),
        "nominee_name": execution_vote_state.get("nominee_name"),
        "required_votes_cast": sum(1 for voter in current_votes if voter in required_voters),
        "required_votes_total": len(required_voters),
        "yes_votes": sum(1 for vote in current_votes.values() if vote == "yes"),
        "no_votes": sum(1 for vote in current_votes.values() if vote == "no"),
        "server_ts": int(time.time() * 1000),
    }


def log_assigned_characters_summary(game_selection, event_label=None):
    if not game_selection:
        print("[character-summary] Brak danych do podsumowania.")
        return

    log_title = "Przydzial postaci"
    if event_label:
        log_title = f"{log_title} ({event_label})"

    print(f"\n[character-summary] {log_title}:")
    print("[character-summary]" + "-" * 101)
    print(
        "[character-summary] {:<14} | {:<20} | {:<24} | {:<5} | {:<8}".format(
            "Kategoria",
            "Postac",
            "Gracz",
            "Seat",
            "Status",
        )
    )
    print("[character-summary]" + "-" * 101)

    sorted_players = sorted(
        db_players.get_all().items(),
        key=lambda item: (
            item[1].get("seat") is None,
            item[1].get("seat") if item[1].get("seat") is not None else 9999,
            item[1].get("name", "Nieznany"),
        ),
    )

    for client_id, player in sorted_players:
        assigned_category = "brak"
        assigned_role = "brak"

        for category in ["Mieszkańcy", "Outsiderzy", "Minionki", "Demon"]:
            for char in game_selection.get(category, []):
                if char.get("client_id") == client_id:
                    assigned_category = category
                    assigned_role = char.get("name", "Nieznana")
                    break
            if assigned_role != "brak":
                break

        player_name = player.get("name", "Nieznany")
        seat = player.get("seat", "brak")
        status = "martwy" if player.get("executed") else "zywy"

        print(
            "[character-summary] {:<14} | {:<20} | {:<24} | {:<5} | {:<8}".format(
                assigned_category,
                assigned_role,
                player_name,
                seat,
                status,
            )
        )

    print("[character-summary]" + "-" * 101)


def is_seat_taken(seat, excluded_client_id=None):
    for existing_client_id, player in db_players.get_all().items():
        if existing_client_id == excluded_client_id:
            continue
        if player.get("seat") == seat:
            return True

    return False


def build_game_status_payload():
    imp_required = False
    imp_client_id = get_current_imp_client_id()
    if imp_client_id and imp_client_id in db_players:
        ensure_player_flags(db_players[imp_client_id])
        imp_required = not db_players[imp_client_id]["executed"]

    truciciel_required = False
    truciciel_character = get_truciciel_character()
    if truciciel_character:
        truciciel_client_id = truciciel_character.get("client_id")
        if truciciel_client_id in db_players:
            ensure_player_flags(db_players[truciciel_client_id])
            truciciel_required = not db_players[truciciel_client_id]["executed"]

    imp_done = db_game.get("imp_action_done_night", False)
    truciciel_done = db_game.get("truciciel_action_done_night", False)
    night_actions_pending = db_game.get("mode") == "night" and (
        (imp_required and not imp_done)
        or (truciciel_required and not truciciel_done)
    )

    return {
        "no_of_players": len(db_players),
        "game_status": db_game["game_active"],
        "game_active": db_game["game_active"],
        "char_presented": db_game["char_presented"],
        "mode": db_game["mode"],
        "day_number": db_game.get("day_number", 1),
        "imp_action_done_night": imp_done,
        "truciciel_action_done_night": truciciel_done,
        "night_actions_pending": night_actions_pending,
        "winner": db_game.get("winner"),
        "execution_vote_active": execution_vote_state["active"],
    }


def build_minion_night_status():
    if not db_game_selection:
        return "Brak aktywnej rozgrywki."

    minion_names = []
    for char in db_game_selection.get("Minionki", []):
        minion_client_id = char.get("client_id")
        if minion_client_id in db_players:
            minion_names.append(db_players[minion_client_id].get("name", "Nieznany"))

    imp_name = "Nieznany"
    for char in db_game_selection.get("Demon", []):
        if char.get("name") == "Imp" and char.get("client_id") in db_players:
            imp_name = db_players[char.get("client_id")].get("name", "Nieznany")
            break

    minions_text = ", ".join(minion_names) if minion_names else "Brak Minionków"
    return (
        f"Minionki w grze: {minions_text}.\n"
        f"Imp w grze: {imp_name}."
    )


def get_truciciel_character():
    if not db_game_selection:
        return None

    for char in db_game_selection.get("Minionki", []):
        if char.get("name") == "Truciciel" and char.get("client_id") in db_players:
            return char

    return None


def is_client_poisoned_today(client_id, day_number=None):
    if not client_id:
        return False

    truciciel_character = get_truciciel_character()
    if not truciciel_character:
        return False

    if day_number is None:
        day_number = db_game.get("day_number", 1)

    poison_targets_by_day = truciciel_character.get("truciciel_poison_targets_by_day", {})
    poisoned_client_id = poison_targets_by_day.get(str(day_number))
    return poisoned_client_id == client_id


def invalidate_dynamic_statuses():
    if not db_game_selection:
        return

    for characters in db_game_selection.values():
        for character in characters:
            player_status_field = character.get("player_status")
            if not callable(player_status_field):
                continue

            try:
                signature = inspect.signature(player_status_field)
            except (TypeError, ValueError):
                continue

            if any(param in signature.parameters for param in {"mode", "day_number", "poisoned"}):
                character.pop("resolved_player_status", None)
                character.pop("resolved_player_status_key", None)


def get_current_imp_client_id():
    if not db_game_selection:
        return None

    for char in db_game_selection.get("Demon", []):
        if char.get("name") == "Imp" and char.get("client_id") in db_players:
            return char.get("client_id")

    return None


def get_alive_good_count():
    if not db_game_selection:
        return 0

    alive_player_ids = set(get_alive_player_ids())
    alive_good_ids = {
        char.get("client_id")
        for char in (db_game_selection.get("Mieszkańcy", []) + db_game_selection.get("Outsiderzy", []))
        if char.get("client_id") in alive_player_ids
    }
    return len(alive_good_ids)


def evaluate_and_finalize_game_if_needed():
    if db_game.get("winner"):
        return True

    imp_client_id = get_current_imp_client_id()
    if imp_client_id:
        ensure_player_flags(db_players[imp_client_id])
        if db_players[imp_client_id]["executed"]:
            db_game["winner"] = "good"
            db_game["game_active"] = False
            message = "Imp został wyeliminowany. Wygrywają Dobrzy (Mieszkańcy + Outsiderzy)."
            socketio.emit("game_over", {"winner": "good", "message": message})
            socketio.emit("update_game_status", build_game_status_payload())
            redirect_players_to_endpoint("menu_koniec_gry")
            return True

    if get_alive_good_count() == 0:
        db_game["winner"] = "evil"
        db_game["game_active"] = False
        message = "W grze nie ma już żywych dobrych graczy. Wygrywają Źli (Minionki + Demon)."
        socketio.emit("game_over", {"winner": "evil", "message": message})
        socketio.emit("update_game_status", build_game_status_payload())
        redirect_players_to_endpoint("menu_koniec_gry")
        return True

    alive_players = get_alive_player_ids()
    if len(alive_players) <= 2:
        db_game["winner"] = "evil"
        db_game["game_active"] = False
        message = "W grze pozostało 2 lub mniej żywych graczy. Wygrywają Źli (Minionki + Demon)."
        socketio.emit("game_over", {"winner": "evil", "message": message})
        socketio.emit("update_game_status", build_game_status_payload())
        redirect_players_to_endpoint("menu_koniec_gry")
        return True

    return False


def reset_all_game_state():
    global db_game_selection

    db_game_selection = None

    db_game["game_active"] = False
    db_game["char_presented"] = False
    db_game["mode"] = "day"
    db_game["day_number"] = 1
    db_game["no_of_players"] = 0
    db_game["admin_id"] = None
    db_game["players"] = []
    db_game["winner"] = None
    db_game["nominator_last_day"] = {}
    db_game["imp_action_done_night"] = False
    db_game["truciciel_action_done_night"] = False

    clients.clear()
    db_players._data.clear()
    db_players._sid_index.clear()

    execution_vote_state["vote_id"] = 0
    execution_vote_state["last_result"] = None
    reset_execution_vote_state()


def reset_execution_vote_state():
    execution_vote_state["active"] = False
    execution_vote_state["nominator_client_id"] = None
    execution_vote_state["nominator_name"] = None
    execution_vote_state["nominator_seat"] = None
    execution_vote_state["nominee_client_id"] = None
    execution_vote_state["nominee_name"] = None
    execution_vote_state["votes"] = {}
    execution_vote_state["required_voters"] = []
    execution_vote_state["optional_voters"] = []


def emit_execution_vote_started():
    for client_id in db_players.get_all_client_ids():
        player = db_players[client_id]
        ensure_player_flags(player)
        sid = player.get("sid")
        if not sid:
            continue

        can_vote = (not player["executed"]) or player["vote_dead"]
        socketio.emit(
            "execution_vote_started",
            {
                "nominee_client_id": execution_vote_state["nominee_client_id"],
                "nominee_name": execution_vote_state["nominee_name"],
                "can_vote": can_vote,
            },
            to=sid,
        )


def emit_execution_vote_result(message, yes_votes, no_votes, executed):
    for client_id in db_players.get_all_client_ids():
        player = db_players[client_id]
        ensure_player_flags(player)
        sid = player.get("sid")
        if not sid:
            continue

        socketio.emit(
            "execution_vote_result",
            {
                "vote_id": execution_vote_state.get("vote_id", 0),
                "message": message,
                "yes_votes": yes_votes,
                "no_votes": no_votes,
                "executed": executed,
                "player_flags": {
                    "executed": player["executed"],
                    "vote_dead": player["vote_dead"],
                },
            },
            to=sid,
        )


def emit_execution_vote_progress():
    if not execution_vote_state["active"]:
        return

    required_voters = set(execution_vote_state["required_voters"])
    optional_voters = set(execution_vote_state["optional_voters"])
    current_votes = execution_vote_state["votes"]

    required_votes_cast = sum(1 for voter in current_votes if voter in required_voters)
    yes_votes = sum(1 for vote in current_votes.values() if vote == "yes")
    no_votes = sum(1 for vote in current_votes.values() if vote == "no")

    for client_id in db_players.get_all_client_ids():
        player = db_players[client_id]
        sid = player.get("sid")
        if not sid:
            continue

        can_vote = (
            client_id in required_voters or client_id in optional_voters
        ) and client_id not in current_votes

        socketio.emit(
            "execution_vote_progress",
            {
                "vote_id": execution_vote_state.get("vote_id", 0),
                "required_votes_cast": required_votes_cast,
                "required_votes_total": len(required_voters),
                "yes_votes": yes_votes,
                "no_votes": no_votes,
                "can_vote": can_vote,
                "has_voted": client_id in current_votes,
            },
            to=sid,
        )


def submit_execution_vote(voter_client_id, raw_vote):
    normalized_vote = str(raw_vote or "").strip().lower()

    if normalized_vote in {"tak", "yes", "true", "1"}:
        vote = "yes"
    elif normalized_vote in {"nie", "no", "false", "0"}:
        vote = "no"
    else:
        return "Niepoprawny głos. Użyj TAK lub NIE."

    if not execution_vote_state["active"]:
        return "Aktualnie nie trwa żadne głosowanie."

    if not voter_client_id or voter_client_id not in db_players:
        return "Nie znaleziono gracza głosującego."

    if voter_client_id in execution_vote_state["votes"]:
        return "Ten gracz już oddał głos."

    required_voters = set(execution_vote_state["required_voters"])
    optional_voters = set(execution_vote_state["optional_voters"])

    if voter_client_id not in required_voters and voter_client_id not in optional_voters:
        return "Ten gracz nie może oddać głosu w tym głosowaniu."

    ensure_player_flags(db_players[voter_client_id])
    if voter_client_id in optional_voters and vote == "yes":
        db_players[voter_client_id]["vote_dead"] = False

    execution_vote_state["votes"][voter_client_id] = vote
    emit_execution_vote_progress()
    finalize_execution_vote_if_ready()
    return None


def perform_truciciel_night_action(actor_client_id, target_client_id):
    if not db_game_selection:
        return "Brak aktywnej rozgrywki.", None

    if db_game.get("mode") != "night":
        return "Akcja Truciciela jest dostępna tylko w nocy.", None

    if not actor_client_id or actor_client_id not in db_players:
        return "Nie znaleziono gracza wykonującego akcję.", None

    if not target_client_id or target_client_id not in db_players:
        return "Nie znaleziono wybranego celu.", None

    ensure_player_flags(db_players[actor_client_id])
    if db_players[actor_client_id]["executed"]:
        return "Wyeliminowany Truciciel nie może wykonać akcji.", None

    real_character, _ = get_player_character_views(actor_client_id)
    if not real_character or real_character.get("name") != "Truciciel":
        return "Tylko Truciciel może wykonać tę akcję.", None

    if db_game.get("truciciel_action_done_night"):
        return "Akcja Truciciela została już wykonana tej nocy.", None

    day_number = db_game.get("day_number", 1)

    poison_targets_by_day = real_character.setdefault("truciciel_poison_targets_by_day", {})
    next_day = day_number + 1
    poison_targets_by_day[str(next_day)] = target_client_id

    real_character["truciciel_last_night_used"] = day_number
    real_character["truciciel_last_selected_target_client_id"] = target_client_id
    real_character.pop("resolved_player_status", None)
    real_character.pop("resolved_player_status_key", None)

    db_game["truciciel_action_done_night"] = True
    socketio.emit("update_game_status", build_game_status_payload())
    socketio.emit("force_player_page_refresh", {})

    target_name = db_players[target_client_id].get("name", "Nieznany")
    result_message = (
        f"Wybrałeś cel zatrucia: {target_name}. "
        f"Efekt zatrucia będzie aktywny od dnia {next_day}."
    )
    return None, result_message


def perform_jasnowidz_day_action(actor_client_id, first_target_client_id, second_target_client_id):
    if not db_game_selection:
        return "Brak aktywnej rozgrywki.", None

    if db_game.get("mode") != "day":
        return "Akcja Jasnowidza jest dostępna tylko w dzień.", None

    if not actor_client_id or actor_client_id not in db_players:
        return "Nie znaleziono gracza wykonującego akcję.", None

    if not first_target_client_id or first_target_client_id not in db_players:
        return "Nie znaleziono pierwszego celu.", None

    if not second_target_client_id or second_target_client_id not in db_players:
        return "Nie znaleziono drugiego celu.", None

    if first_target_client_id == second_target_client_id:
        return "Wybierz dwóch różnych graczy.", None

    ensure_player_flags(db_players[actor_client_id])
    if db_players[actor_client_id]["executed"]:
        return "Wyeliminowany Jasnowidz nie może wykonać akcji.", None

    real_character, _ = get_player_character_views(actor_client_id)
    if not real_character or real_character.get("name") != "Jasnowidz":
        return "Tylko Jasnowidz może wykonać tę akcję.", None

    day_number = db_game.get("day_number", 1)
    if real_character.get("jasnowidz_last_day_used") == day_number:
        return "Dzisiaj wykorzystałeś już pytanie Jasnowidza.", None

    imp_client_ids = {
        char.get("client_id")
        for char in db_game_selection.get("Demon", [])
        if char.get("name") == "Imp" and char.get("client_id") in db_players
    }

    target_pair = {first_target_client_id, second_target_client_id}
    has_imp = any(client_id in imp_client_ids for client_id in target_pair)

    if is_client_poisoned_today(actor_client_id, day_number):
        has_imp = random.choice([True, False])

    answer = "TAK" if has_imp else "NIE"

    first_name = db_players[first_target_client_id].get("name", "Nieznany")
    second_name = db_players[second_target_client_id].get("name", "Nieznany")
    result_message = (
        f"Pytanie o parę ({first_name}, {second_name}) -> Czy jest tam Imp? {answer}."
    )

    real_character["jasnowidz_last_day_used"] = day_number
    real_character["jasnowidz_daily_result"] = result_message
    real_character.pop("resolved_player_status", None)
    real_character.pop("resolved_player_status_key", None)

    return None, result_message


def perform_imp_night_action(actor_client_id, target_client_id):
    if not db_game_selection:
        return "Brak aktywnej rozgrywki.", None

    if db_game.get("mode") != "night":
        return "Akcja Impa jest dostępna tylko w nocy.", None

    if db_game.get("imp_action_done_night"):
        return "Akcja Impa została już wykonana tej nocy.", None

    if not actor_client_id or actor_client_id not in db_players:
        return "Nie znaleziono gracza wykonującego akcję.", None

    if not target_client_id or target_client_id not in db_players:
        return "Nie znaleziono wybranego celu.", None

    ensure_player_flags(db_players[actor_client_id])
    if db_players[actor_client_id]["executed"]:
        return "Wyeliminowany Imp nie może wykonać akcji.", None

    real_character, _ = get_player_character_views(actor_client_id)
    if not real_character or real_character.get("name") != "Imp":
        return "Tylko Imp może wykonać tę akcję.", None

    imp_character = None
    for char in db_game_selection.get("Demon", []):
        if char.get("name") == "Imp" and char.get("client_id") == actor_client_id:
            imp_character = char
            break

    if not imp_character:
        return "Nie znaleziono aktywnej postaci Impa.", None

    swap_message = ""
    if target_client_id == actor_client_id:
        minion_candidates = [
            char for char in db_game_selection.get("Minionki", [])
            if char.get("client_id") in db_players and char.get("client_id") != actor_client_id
        ]
        if minion_candidates:
            chosen_minion = random.choice(minion_candidates)
            chosen_minion_client_id = chosen_minion.get("client_id")
            imp_character["client_id"], chosen_minion["client_id"] = (
                chosen_minion_client_id,
                actor_client_id,
            )
            swap_message = (
                " Wybrałeś siebie - nastąpiła losowa zamiana ról Impa i Minionka "
                f"z graczem {db_players[actor_client_id].get('name', 'Nieznany')} "
                f"oraz {db_players[chosen_minion_client_id].get('name', 'Nieznany')}."
            )

    ensure_player_flags(db_players[target_client_id])
    target_was_executed = db_players[target_client_id]["executed"]
    db_players[target_client_id]["executed"] = True

    if not target_was_executed:
        log_assigned_characters_summary(db_game_selection, event_label="status zmieniony na martwy")

    db_game["imp_action_done_night"] = True
    socketio.emit("update_game_status", build_game_status_payload())

    for group_chars in db_game_selection.values():
        for char in group_chars:
            char.pop("resolved_player_status", None)

    target_name = db_players[target_client_id].get("name", "Nieznany")
    result_message = f"Akcja Impa wykonana. Wyeliminowano gracza: {target_name}.{swap_message}"
    socketio.emit("force_player_page_refresh", {})
    evaluate_and_finalize_game_if_needed()

    return None, result_message


def finalize_execution_vote_if_ready(force=False):
    if not execution_vote_state["active"]:
        return

    required_voters = set(execution_vote_state["required_voters"])
    current_votes = execution_vote_state["votes"]
    required_voters_voted = {client_id for client_id in current_votes if client_id in required_voters}

    if not force and required_voters_voted != required_voters:
        return

    yes_votes = sum(1 for vote in current_votes.values() if vote == "yes")
    no_votes = sum(1 for vote in current_votes.values() if vote == "no")
    nominee_client_id = execution_vote_state["nominee_client_id"]
    nominee_name = execution_vote_state["nominee_name"]

    player_executed = False
    if yes_votes > no_votes and nominee_client_id in db_players:
        ensure_player_flags(db_players[nominee_client_id])
        nominee_was_executed = db_players[nominee_client_id]["executed"]
        db_players[nominee_client_id]["executed"] = True
        player_executed = True

        if db_game_selection:
            for group_chars in db_game_selection.values():
                for char in group_chars:
                    char.pop("resolved_player_status", None)
                    char.pop("resolved_player_status_key", None)

        if not nominee_was_executed:
            log_assigned_characters_summary(db_game_selection, event_label="status zmieniony na martwy")

    if player_executed:
        message = f"Gracz {nominee_name} został wyeliminowany z gry."
    else:
        message = f"Gracz {nominee_name} nie został wyeliminowany (większość NIE lub remis)."

    execution_vote_state["last_result"] = {
        "vote_id": execution_vote_state.get("vote_id", 0),
        "nominator_name": execution_vote_state.get("nominator_name") or "Nieznany",
        "nominator_seat": execution_vote_state.get("nominator_seat"),
        "nominee_name": nominee_name,
        "message": message,
        "yes_votes": yes_votes,
        "no_votes": no_votes,
        "executed": player_executed,
        "required_votes_total": len(required_voters),
    }

    emit_execution_vote_result(message, yes_votes, no_votes, player_executed)
    reset_execution_vote_state()
    evaluate_and_finalize_game_if_needed()


def try_start_execution_vote(nominator_client_id, nominee_client_id):
    day_number = db_game.get("day_number", 1)
    print(
        "[nomination] attempt "
        f"day={day_number} nominator={nominator_client_id} nominee={nominee_client_id}"
    )

    if execution_vote_state["active"]:
        print(
            "[nomination] reject "
            f"day={day_number} nominator={nominator_client_id} reason=active_vote"
        )
        return "Trwa już inne głosowanie."

    if not nominator_client_id or nominator_client_id not in db_players:
        print(
            "[nomination] reject "
            f"day={day_number} nominator={nominator_client_id} reason=missing_nominator"
        )
        return "Nie znaleziono nominującego gracza."

    ensure_player_flags(db_players[nominator_client_id])
    if db_players[nominator_client_id]["executed"]:
        print(
            "[nomination] reject "
            f"day={day_number} nominator={nominator_client_id} reason=nominator_executed"
        )
        return "Gracz wyeliminowany nie może nominować."

    nominator_last_day = db_game.setdefault("nominator_last_day", {})
    if nominator_last_day.get(nominator_client_id) == day_number:
        print(
            "[nomination] reject "
            f"day={day_number} nominator={nominator_client_id} reason=already_nominated_today"
        )
        return "Ten gracz może nominować tylko raz w ciągu dnia."

    if not nominee_client_id or nominee_client_id not in db_players:
        print(
            "[nomination] reject "
            f"day={day_number} nominator={nominator_client_id} nominee={nominee_client_id} "
            "reason=missing_nominee"
        )
        return "Nie znaleziono nominowanego gracza."

    ensure_player_flags(db_players[nominee_client_id])
    if db_players[nominee_client_id]["executed"]:
        print(
            "[nomination] reject "
            f"day={day_number} nominator={nominator_client_id} nominee={nominee_client_id} "
            "reason=nominee_executed"
        )
        return "Nie można nominować gracza już wyeliminowanego."

    execution_vote_state["active"] = True
    execution_vote_state["vote_id"] = execution_vote_state.get("vote_id", 0) + 1
    execution_vote_state["last_result"] = None
    execution_vote_state["nominator_client_id"] = nominator_client_id
    execution_vote_state["nominator_name"] = db_players[nominator_client_id].get("name", "Nieznany")
    execution_vote_state["nominator_seat"] = db_players[nominator_client_id].get("seat")
    execution_vote_state["nominee_client_id"] = nominee_client_id
    execution_vote_state["nominee_name"] = db_players[nominee_client_id].get("name", "Nieznany")
    execution_vote_state["votes"] = {}
    execution_vote_state["required_voters"] = get_alive_player_ids()
    execution_vote_state["optional_voters"] = get_optional_dead_voter_ids()
    nominator_last_day[nominator_client_id] = day_number

    print(
        "[nomination] accepted "
        f"day={day_number} nominator={nominator_client_id} nominee={nominee_client_id} "
        f"vote_id={execution_vote_state['vote_id']}"
    )

    emit_execution_vote_started()
    emit_execution_vote_progress()
    redirect_players_to_endpoint("execution_vote_page")
    return None
    if player_executed:
        check_and_announce_evil_win_if_needed()


def handle_player_removed_from_execution_vote(client_id):
    if not execution_vote_state["active"]:
        return

    execution_vote_state["votes"].pop(client_id, None)
    execution_vote_state["required_voters"] = [
        voter for voter in execution_vote_state["required_voters"] if voter != client_id
    ]
    execution_vote_state["optional_voters"] = [
        voter for voter in execution_vote_state["optional_voters"] if voter != client_id
    ]

    if execution_vote_state["nominee_client_id"] == client_id:
        emit_execution_vote_result(
            "Głosowanie anulowane, bo nominowany gracz opuścił grę.",
            0,
            0,
            False,
        )
        reset_execution_vote_state()
        return

    finalize_execution_vote_if_ready()


def remove_player_from_game(client_id):
    if client_id not in db_players:
        return False

    handle_player_removed_from_execution_vote(client_id)

    clients.pop(client_id, None)
    db_players.remove(client_id)

    if client_id in db_game["players"]:
        db_game["players"].remove(client_id)

    db_game["no_of_players"] = len(db_players)
    evaluate_and_finalize_game_if_needed()
    return True


def seed_default_players_for_admin():
    for default_player in DEFAULT_TEST_PLAYERS:
        client_id = default_player["client_id"]
        if client_id in db_players:
            continue

        db_players.add(
            client_id,
            {
                "name": default_player["name"],
                "character": "test",
                "seat": default_player["seat"],
                "executed": default_player["executed"],
                "vote_dead": default_player["vote_dead"],
                "sid": None,
            },
        )


def remove_default_test_players():
    for default_player in DEFAULT_TEST_PLAYERS:
        default_client_id = default_player["client_id"]
        if default_client_id in db_players:
            remove_player_from_game(default_client_id)


def resolve_back_endpoint(default_endpoint="index"):
    requested_endpoint = request.args.get("back")
    if requested_endpoint in ALLOWED_BACK_ENDPOINTS:
        return requested_endpoint

    client_id = session.get("client_id")
    if client_id in db_players:
        return "lobby"
    if client_id == db_game.get("admin_id"):
        return "handle_menu"
    return default_endpoint


def get_resume_redirect_endpoint(client_id):
    if not client_id:
        return None

    if db_game.get("winner"):
        return "menu_koniec_gry"

    if client_id == db_game.get("admin_id"):
        if db_game.get("char_presented") and db_game_selection:
            return "player_page"
        return "handle_menu"

    if client_id in db_players:
        if db_game.get("char_presented") and db_game_selection:
            return "player_page"
        return "lobby"

    return None

@socketio.on('connect')
def handle_connect():
    sid = request.sid
    print(f"Nowe połączenie: {sid}")

@socketio.on('client_id_response')
def handle_client_id(data):
    sid = request.sid
    client_id = data.get("client_id") or data.get("clientId")

    print(f"Otrzymano client_id={client_id} dla sid={sid}")
    if client_id:
        clients[client_id] = sid

    # Jeśli gracz już istnieje po client_id, aktualizujemy SID
    if client_id in db_players:
        print("Znaleziono istniejącego gracza, aktualizuję SID...")
        player = db_players[client_id]
        player["sid"] = sid

@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    print(f"🔴 Rozłączono: {sid}")

    disconnected_client_id = None
    for client_id, active_sid in list(clients.items()):
        if active_sid == sid:
            disconnected_client_id = client_id
            clients.pop(client_id, None)
            break

    if disconnected_client_id and disconnected_client_id in db_players:
        db_players[disconnected_client_id]["sid"] = None
        print(f"[disconnect] Wyczyszczono sid dla client_id={disconnected_client_id}")


@socketio.on("request_nomination_candidates")
def handle_request_nomination_candidates(data):
    client_id = data.get("clientId") or data.get("client_id")
    print(f"[nomination/socket] request_nomination_candidates client_id={client_id}")
    payload = build_nomination_candidates_payload(client_id)
    emit("nomination_candidates", payload)


@socketio.on("start_execution_vote")
def handle_start_execution_vote(data):
    nominator_client_id = data.get("clientId") or data.get("client_id")
    nominee_client_id = data.get("nominee_client_id")
    print(
        "[nomination/socket] start_execution_vote "
        f"nominator_client_id={nominator_client_id}, nominee_client_id={nominee_client_id}"
    )

    error = try_start_execution_vote(nominator_client_id, nominee_client_id)
    if error:
        emit("execution_vote_error", {"error": error})


@socketio.on("cast_execution_vote")
def handle_cast_execution_vote(data):
    voter_client_id = data.get("clientId") or data.get("client_id")
    error = submit_execution_vote(voter_client_id, data.get("vote"))
    if error:
        emit("execution_vote_error", {"error": error})


@socketio.on("imp_night_action")
def handle_imp_night_action(data):
    actor_client_id = data.get("clientId") or data.get("client_id")
    target_client_id = data.get("target_client_id")

    error, result_message = perform_imp_night_action(actor_client_id, target_client_id)
    if error:
        emit("imp_action_error", {"error": error})
        return

    emit("imp_action_result", {"message": result_message})


@socketio.on("jasnowidz_day_action")
def handle_jasnowidz_day_action(data):
    actor_client_id = data.get("clientId") or data.get("client_id")
    first_target_client_id = data.get("first_target_client_id")
    second_target_client_id = data.get("second_target_client_id")
    error, result_message = perform_jasnowidz_day_action(
        actor_client_id,
        first_target_client_id,
        second_target_client_id,
    )
    if error:
        emit("jasnowidz_action_error", {"error": error})
        return

    emit("jasnowidz_action_result", {"message": result_message})
    emit("force_player_page_refresh", {})


@socketio.on("truciciel_day_action")
def handle_truciciel_day_action(data):
    actor_client_id = data.get("clientId") or data.get("client_id")
    target_client_id = data.get("target_client_id")

    error, result_message = perform_truciciel_night_action(actor_client_id, target_client_id)
    if error:
        emit("truciciel_action_error", {"error": error})
        return

    emit("truciciel_action_result", {"message": result_message})
    emit("force_player_page_refresh", {})
        
@app.route("/")
def index():
    client_id = session.get("client_id")
    redirect_endpoint = get_resume_redirect_endpoint(client_id)
    if redirect_endpoint:
        return redirect(url_for(redirect_endpoint))

    if client_id and client_id in db_players:
        return render_template(
            "index.html",
            name=db_players[client_id]["name"],
            numer_miejsca=db_players[client_id].get("seat", ""),
        )
    else:
        return render_template("index.html", name="", numer_miejsca="")


@app.route("/resume-session", methods=["POST"])
def resume_session():
    data = request.get_json(silent=True) or {}
    client_id = data.get("clientId") or data.get("client_id")
    redirect_endpoint = get_resume_redirect_endpoint(client_id)

    if not redirect_endpoint:
        return jsonify({"status": "not-found"}), 404

    session["client_id"] = client_id
    return redirect(url_for(redirect_endpoint))

@app.route("/save-player", methods=["POST"])
def save_player():
    data = request.get_json()
    name = data.get("name")
    raw_seat = data.get("numer_miejsca")
    moderator_login_requested = bool(data.get("moderator_login"))
    moderator_password = str(data.get("moderator_password") or "")
    client_id = data.get("clientId") or data.get("client_id")
    socket_sid = data.get("socketSid")
    session["client_id"] = client_id
    is_moderator_login = moderator_login_requested and moderator_password == "secret"
    is_admin_login = name == "admin" or is_moderator_login
    requires_seat = (not is_admin_login) or is_moderator_login
    print(
        f"Save {name=}, {raw_seat=}, {moderator_login_requested=}, "
        f"{client_id=}, {socket_sid=}"
    )
    
    if client_id:
        if not name:
            return jsonify({"error": "Brak wymaganych danych"}), 400

        if moderator_login_requested and moderator_password != "secret":
            return jsonify({"error": "Nieprawidłowe hasło moderatora"}), 400

        seat = None
        if requires_seat:
            try:
                seat = parse_seat(raw_seat)
            except ValueError as exc:
                return jsonify({"error": str(exc)}), 400

        elif str(raw_seat or "").strip():
            try:
                seat = parse_seat(raw_seat)
            except ValueError as exc:
                return jsonify({"error": str(exc)}), 400

        if seat is not None:
            if is_seat_taken(seat, excluded_client_id=client_id):
                return jsonify({"error": f"Miejsce numer {seat} jest już zajęte"}), 400

        if is_admin_login:
            db_game["admin_id"] = client_id
            if test_enabled:
                print("Testowy login administratora - dodaję domyślnych graczy do bazy")
                seed_default_players_for_admin()
            else:
                remove_default_test_players()

        if client_id not in db_players:
            print(f"Dodaje nowego gracza: {name}, seat: {seat}")
            db_players.add(client_id, { "name" : None, "character" : None, "seat": None, "executed": False, "vote_dead": True, "sid": None} )

        db_players[client_id]["name"] = name
        db_players[client_id]["character"] = "admin" if is_admin_login else ""
        db_players[client_id]["seat"] = seat
        db_players[client_id].setdefault("executed", False)
        db_players[client_id].setdefault("vote_dead", True)

        if socket_sid:
            clients[client_id] = socket_sid
            db_players[client_id]["sid"] = socket_sid
            print(f"[save_player] Ustawiono sid z payloadu: sid={socket_sid} dla client_id={client_id}")
        elif client_id in clients:
            db_players[client_id]["sid"] = clients[client_id]
            print(f"[save_player] Przepisano aktywny sid={clients[client_id]} do client_id={client_id}")
        else:
            print(f"[save_player] Brak aktywnego sid dla client_id={client_id} w chwili zapisu gracza")
        
        db_game["no_of_players"] = len(db_players)
        socketio.emit("update_game_status", build_game_status_payload())
        print("Aktualna baza graczy:", db_players._data)

        if is_admin_login:
            if db_game.get("char_presented") and db_game_selection:
                return redirect(url_for("player_page"))
            return redirect(url_for("handle_menu"))

        return redirect(url_for("lobby"))
    else:
        print(f"Unknown {client_id=}")
        return redirect(url_for("index"))

@app.route("/lobby")
def lobby():
    client_id = session.get("client_id")
    try:
        person = db_players[client_id]["name"]
    except:
        return redirect(url_for("index"))
    
    if db_game["game_active"] == False:
        return render_template("lobby.html", 
                               greetings=f"Miło Cię widzieć {person}",
                               room_status="Gra się nie rozpoczęła. Czekaj na administratora aż rozpocznie grę.",
                               no_of_player= len(db_players),
                               players=len(db_players))
    else:
        no_of_players=len(db_rooms["players"])
        return render_template("lobby.html", 
                               greetings=f"Miło Cię widzieć {person}",
                               room_status=f"Gra przygotowana, oczekuj na losowanie postaci.",
                               no_of_players= len(db_players),
                               players=len(db_players))


@app.route("/game-status", methods=["GET"])
def game_status():
    client_id = session.get("client_id")
    is_player = bool(client_id and client_id in db_players)
    status_payload = build_game_status_payload()

    response = jsonify({
        "no_of_players": len(db_players),
        "game_active": status_payload["game_active"],
        "char_presented": status_payload["char_presented"],
        "mode": status_payload["mode"],
        "day_number": status_payload.get("day_number", 1),
        "imp_action_done_night": status_payload.get("imp_action_done_night", False),
        "truciciel_action_done_night": status_payload.get("truciciel_action_done_night", False),
        "night_actions_pending": status_payload.get("night_actions_pending", False),
        "winner": status_payload.get("winner"),
        "execution_vote_active": status_payload["execution_vote_active"],
        "is_player": is_player,
        "server_ts": int(time.time() * 1000),
    })
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response, 200


@app.route("/execution-vote-status", methods=["GET"])
def execution_vote_status():
    session_client_id = session.get("client_id")
    client_id = session_client_id or request.args.get("client_id")
    if not client_id or client_id not in db_players:
        return jsonify({"error": "Brak aktywnej sesji gracza."}), 401

    vote_context = build_execution_vote_page_context(client_id)
    if not vote_context:
        return jsonify({"active": False, "last_result": execution_vote_state.get("last_result")}), 200

    return jsonify({"active": True, "vote_context": vote_context}), 200


@app.route("/execution-vote-public-status", methods=["GET"])
def execution_vote_public_status():
    response = jsonify(build_execution_vote_public_status())
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response, 200


@app.route("/nomination-candidates", methods=["GET"])
def nomination_candidates():
    session_client_id = session.get("client_id")
    client_id = session_client_id or request.args.get("client_id")
    print(
        "[nomination/http] nomination-candidates "
        f"session_client_id={session_client_id}, requested_client_id={client_id}"
    )

    if not client_id:
        return jsonify({"error": "Brak aktywnej sesji gracza."}), 401

    payload = build_nomination_candidates_payload(client_id)
    status_code = 200 if "error" not in payload else 400
    return jsonify(payload), status_code


@app.route("/start-execution-vote", methods=["POST"])
def start_execution_vote_http():
    payload = request.get_json(silent=True) or {}
    session_client_id = session.get("client_id")
    nominator_client_id = session_client_id or payload.get("client_id") or payload.get("clientId")
    nominee_client_id = payload.get("nominee_client_id")
    print(
        "[nomination/http] start-execution-vote "
        f"session_client_id={session_client_id}, nominator_client_id={nominator_client_id}, "
        f"nominee_client_id={nominee_client_id}"
    )

    if not nominator_client_id:
        return jsonify({"error": "Brak aktywnej sesji gracza."}), 401

    error = try_start_execution_vote(nominator_client_id, nominee_client_id)
    if error:
        return jsonify({"error": error}), 400

    ensure_player_flags(db_players[nominator_client_id])
    can_vote = (not db_players[nominator_client_id]["executed"]) or db_players[nominator_client_id]["vote_dead"]

    return jsonify(
        {
            "status": "ok",
            "nominee_client_id": execution_vote_state["nominee_client_id"],
            "nominee_name": execution_vote_state["nominee_name"],
            "can_vote": can_vote,
        }
    ), 200

@app.route("/menu")
def handle_menu():
    client_id = session.get("client_id")
    if db_game.get("winner"):
        return redirect(url_for("menu_koniec_gry"))
    if(client_id != db_game["admin_id"]):
        return redirect(url_for("index"))
    
    return render_template(
        "menu.html",
        liczba_graczy=len(db_players),
        char_presented=db_game["char_presented"],
        current_mode=db_game["mode"],
        imp_action_done_night=db_game.get("imp_action_done_night", False),
        night_actions_pending=build_game_status_payload().get("night_actions_pending", False),
    )


@app.route("/game-mode", methods=["POST"])
def set_game_mode():
    client_id = session.get("client_id")
    if client_id != db_game.get("admin_id"):
        return jsonify({"error": "Brak uprawnień."}), 403

    previous_mode = db_game.get("mode", "day")
    mode = (request.form.get("mode") or "").strip().lower()
    if mode not in {"day", "night"}:
        return jsonify({"error": "Nieprawidłowy tryb gry."}), 400

    if previous_mode == "night" and mode == "day":
        db_game["day_number"] = db_game.get("day_number", 1) + 1
        db_game["imp_action_done_night"] = False
        db_game["truciciel_action_done_night"] = False

    if previous_mode != "night" and mode == "night":
        db_game["imp_action_done_night"] = False
        db_game["truciciel_action_done_night"] = False

    if previous_mode != mode and db_game_selection:
        invalidate_dynamic_statuses()

    db_game["mode"] = mode
    socketio.emit("update_game_status", build_game_status_payload())
    return jsonify({"status": "ok", "mode": mode}), 200
    
@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        event = request.form.get("event")
        client_id = session.get("client_id")
        
        if event == "create":
            db_game["game_active"] = True
            db_game["no_of_players"] = len(db_players)
            db_game["winner"] = None
            db_game["day_number"] = 1
            db_game["nominator_last_day"] = {}
            db_game["imp_action_done_night"] = False
            db_game["truciciel_action_done_night"] = False
            
            socketio.emit("update_game_status", { 
                                                "no_of_players": db_game["no_of_players"], 
                                                "game_status": "Gra przygotowana, oczekuj na losowanie postaci.",
                                                "game_active": db_game["game_active"],
                                                "char_presented": db_game["char_presented"],
                                                "mode": db_game["mode"],
                                                "imp_action_done_night": db_game["imp_action_done_night"],
                                                "truciciel_action_done_night": db_game["truciciel_action_done_night"],
                                                })
        elif event == "show":
            print(f"[create] Otrzymano żądanie losowania postaci od client_id={client_id}")
            if len(db_players) < 5:
                return jsonify({"error": "Too few players. Minimum is 5"}), 404

            db_game["char_presented"] = True
            db_game["no_of_players"] = len(db_players)
            db_game["winner"] = None
            db_game["day_number"] = 1
            db_game["nominator_last_day"] = {}
            db_game["imp_action_done_night"] = False
            db_game["truciciel_action_done_night"] = False
            socketio.emit("update_game_status", { 
                                                "no_of_players": db_game["no_of_players"], 
                                                "game_status": "Postacie zostały rozlosowane.",
                                                "game_active": db_game["game_active"],
                                                "char_presented": db_game["char_presented"],
                                                "mode": db_game["mode"],
                                                "imp_action_done_night": db_game["imp_action_done_night"],
                                                "truciciel_action_done_night": db_game["truciciel_action_done_night"],
                                                })
            
            print("\n\n")
            global db_game_selection
            db_game_selection = assign_players_to_characters(
                db_players.get_all_client_ids(),
                trouble_brewing_setup,
                db_characters,
                db_players.get_all(),
            )
            log_assigned_characters_summary(db_game_selection, event_label="po losowaniu")
            redirect_players_to_character_pages()
            
        return jsonify({"error": "ok"}), 200


@app.route("/leave-game", methods=["POST"])
def leave_game():
    if request.method == "POST":
        room_name = session.get("room")
        print(f"[leave_game] Otrzymano żądanie opuszczenia pokoju: {room_name}")
        
        client_id = session.get("client_id")
        print(f"[leave_game] client_id = {client_id}")

        if not client_id:
            print("[leave_game] Brak client_id w sesji!")
            return redirect(url_for("index"))
        
        if not remove_player_from_game(client_id):
            print(f"[leave_game] Gracza {client_id} nie było w pokoju!")
            return redirect(url_for("index"))

        print(f"[leave_game] Gracz {client_id} usunięty. Pozostali: {db_players.get_all()}")

        if client_id == db_game.get("admin_id"):
            db_game["admin_id"] = None

        session.pop("client_id", None)
        session.pop("room", None)

        socketio.emit("update_game_status", build_game_status_payload())
        
        return redirect(url_for("index"))
    
@app.route("/postac/<route>")
def postac(route):
    back_endpoint = resolve_back_endpoint(default_endpoint="lobby")
    back_url = url_for(back_endpoint)

    for kategoria, postaci in db_characters.items():
        for p in postaci:
            if p["route"] == route:
                return render_template(
                    f"characters/{route}.html",
                    character=p,
                    back_url=back_url,
                )
    abort(404)

@app.route("/wiki")
def handle_wiki():
    back_endpoint = resolve_back_endpoint(default_endpoint="index")
    return render_template(
        "wiki.html",
        characters=db_characters,
        back_endpoint=back_endpoint,
        back_url=url_for(back_endpoint),
    )


def find_character_by_client_id(client_id, db_characters):
    for group_name, characters in db_characters.items():
        for char in characters:
            if char.get("client_id") == client_id:
                return char
    return None


def find_character_template_by_name(role_name):
    if not role_name:
        return None

    for group_name, characters in db_characters.items():
        for char in characters:
            if char.get("name") == role_name:
                return dict(char)

    return None


def get_player_character_views(client_id):
    assigned_characters = []
    for group_name, characters in db_game_selection.items():
        for char in characters:
            if char.get("client_id") == client_id:
                assigned_characters.append(char)

    if not assigned_characters:
        return None, None

    real_character = None
    for char in assigned_characters:
        if char.get("name") == "Pijak":
            real_character = char
            break

    if not real_character:
        for char in assigned_characters:
            if char.get("name") == "Imp":
                real_character = char
                break

    if real_character and real_character.get("name") == "Imp":
        print(
            "[get_player_character_views] Imp priority role view "
            f"client_id={client_id}, role={real_character.get('name')}"
        )
        return real_character, real_character

    if not real_character:
        real_character = assigned_characters[0]
        print(
            "[get_player_character_views] Standard role view "
            f"client_id={client_id}, role={real_character.get('name')}"
        )
        return real_character, real_character

    drunk_role_name = real_character.get("drunk_role_name")
    visible_character = None
    if drunk_role_name:
        for char in assigned_characters:
            if char.get("name") == drunk_role_name:
                visible_character = char
                break

        if not visible_character:
            fallback_character = find_character_template_by_name(drunk_role_name)
            if fallback_character:
                fallback_character["client_id"] = client_id
                fallback_character["numer_siedzenia"] = real_character.get("numer_siedzenia")
                visible_character = fallback_character

    if not visible_character:
        for char in assigned_characters:
            if char.get("name") != "Pijak":
                visible_character = char
                break

    if not visible_character:
        visible_character = real_character

    print(
        "[get_player_character_views] Drunk masking active "
        f"client_id={client_id}, real_role={real_character.get('name')}, "
        f"visible_role={visible_character.get('name')}"
    )
    return real_character, visible_character


def get_stable_player_status(character):
    player_status_field = character.get("player_status")
    if callable(player_status_field):
        kwargs = {}
        cache_key = None
        try:
            signature = inspect.signature(player_status_field)
            if "mode" in signature.parameters:
                kwargs["mode"] = db_game.get("mode", "day")
            if "day_number" in signature.parameters:
                kwargs["day_number"] = db_game.get("day_number", 1)
            if "poisoned" in signature.parameters:
                kwargs["poisoned"] = (
                    db_game.get("mode", "day") == "day"
                    and is_client_poisoned_today(
                        character.get("client_id"),
                        db_game.get("day_number", 1),
                    )
                )
            if kwargs:
                cache_key = tuple(sorted(kwargs.items()))
        except (TypeError, ValueError):
            kwargs = {}
            cache_key = None

        if "resolved_player_status" in character:
            if cache_key is None and character.get("resolved_player_status_key") is None:
                return character["resolved_player_status"]
            if cache_key is not None and character.get("resolved_player_status_key") == cache_key:
                return character["resolved_player_status"]

        resolved_status = player_status_field(db_game_selection, db_players, **kwargs)
        if cache_key is not None:
            character["resolved_player_status_key"] = cache_key
        else:
            character.pop("resolved_player_status_key", None)
    elif isinstance(player_status_field, str):
        if "resolved_player_status" in character:
            return character["resolved_player_status"]
        resolved_status = player_status_field
        character.pop("resolved_player_status_key", None)
    else:
        if "resolved_player_status" in character:
            return character["resolved_player_status"]
        resolved_status = "Brak informacji o statusie postaci."
        character.pop("resolved_player_status_key", None)

    character["resolved_player_status"] = resolved_status
    return resolved_status


def redirect_players_to_character_pages():
    target_client_ids = db_players.get_all_client_ids()

    for client_id in target_client_ids:
        player = db_players[client_id]
        print(f"[redirect_players_to_character_pages] Przetwarzam client_id={client_id}, player={player}")
        print(f"[redirect_players_to_character_pages] player.name={player.get('name')}, player.character={player.get('character')}, player.sid={player.get('sid')}")

    redirect_players_to_endpoint("player_page", target_client_ids=target_client_ids)


@app.route("/player_page")
def player_page():
    client_id = session.get("client_id")
    if client_id == None: 
        return redirect(url_for("index"))
    if db_game.get("winner"):
        return redirect(url_for("menu_koniec_gry"))
    if not db_game_selection:
        return redirect(url_for("index"))
    if execution_vote_state["active"]:
        return redirect(url_for("execution_vote_page"))
    
    real_character, visible_character = get_player_character_views(client_id)
    if not visible_character:
        abort(404, description=f"Brak postaci o client_id={client_id}")

    player_status = get_stable_player_status(visible_character)
    player_info = visible_character["player_info"]
    player_image = f"/static/images/{visible_character['file']}"
    player_link = url_for("postac", route=visible_character["route"], back="player_page")
    ensure_player_flags(db_players[client_id])
    is_imp = bool(real_character and real_character.get("name") == "Imp")
    is_minion = bool(
        real_character
        and any(
            char.get("client_id") == client_id
            for char in db_game_selection.get("Minionki", [])
        )
    )
    is_jasnowidz = bool(real_character and real_character.get("name") == "Jasnowidz")
    is_truciciel = bool(real_character and real_character.get("name") == "Truciciel")
    minion_night_status = build_minion_night_status() if is_minion else ""

    night_players = get_sorted_player_options()

    jasnowidz_used_today = False
    if is_jasnowidz:
        jasnowidz_used_today = real_character.get("jasnowidz_last_day_used") == db_game.get("day_number", 1)

    truciciel_action_done_night = db_game.get("truciciel_action_done_night", False)

    if real_character and real_character.get("name") == "Pijak":
        print(
            "[player_page] Render masked role for Drunk "
            f"client_id={client_id}, visible_role={visible_character.get('name')}"
        )

    return render_template(
        "player_page.html",
        client_id=client_id,
        player_status=player_status,
        player_info=player_info,
        player_image=player_image,
        player_link=player_link,
        is_executed=db_players[client_id]["executed"],
        vote_dead=db_players[client_id]["vote_dead"],
        is_night=(db_game.get("mode") == "night"),
        current_mode=db_game.get("mode", "day"),
        day_number=db_game.get("day_number", 1),
        is_imp=is_imp,
        is_minion=is_minion,
        is_jasnowidz=is_jasnowidz,
        jasnowidz_used_today=jasnowidz_used_today,
        is_truciciel=is_truciciel,
        truciciel_action_done_night=truciciel_action_done_night,
        minion_night_status=minion_night_status,
        imp_action_done_night=db_game.get("imp_action_done_night", False),
        night_actions_pending=build_game_status_payload().get("night_actions_pending", False),
        night_players=night_players,
        is_admin=(client_id == db_game.get("admin_id")),
        liczba_graczy=len(db_players),
        char_presented=db_game.get("char_presented", False),
    )


@app.route("/nomination", methods=["GET", "POST"])
def nomination_page():
    client_id = session.get("client_id")
    if not client_id or client_id not in db_players:
        return redirect(url_for("index"))

    if not db_game_selection:
        return redirect(url_for("player_page"))

    ensure_player_flags(db_players[client_id])
    if db_game.get("mode") != "day":
        return redirect(url_for("player_page"))
    if execution_vote_state["active"]:
        return redirect(url_for("execution_vote_page"))

    error = ""

    if request.method == "POST":
        nominee_client_id = (request.form.get("nominee_client_id") or "").strip()
        error = try_start_execution_vote(client_id, nominee_client_id) or ""
        if not error:
            return redirect(url_for("execution_vote_page"))

    payload = build_nomination_candidates_payload(client_id)
    if payload.get("error"):
        error = payload["error"]
        candidates = []
    else:
        candidates = payload.get("players", [])

    return render_template(
        "nomination.html",
        candidates=candidates,
        error=error,
    )


@app.route("/execution-vote", methods=["GET", "POST"])
def execution_vote_page():
    session_client_id = session.get("client_id")
    request_client_id = (
        request.args.get("client_id")
        or request.form.get("client_id")
        or request.args.get("clientId")
        or request.form.get("clientId")
    )
    client_id = session_client_id or request_client_id

    if not client_id or client_id not in db_players:
        return redirect(url_for("index"))

    if session_client_id != client_id:
        session["client_id"] = client_id

    if not db_game_selection:
        return redirect(url_for("player_page"))

    ensure_player_flags(db_players[client_id])

    if request.method == "POST":
        error = submit_execution_vote(client_id, request.form.get("vote"))
        if error:
            return redirect(url_for("execution_vote_page", error=error, client_id=client_id))
        return redirect(url_for("execution_vote_page", submitted="1", client_id=client_id))

    vote_context = build_execution_vote_page_context(client_id)
    if not vote_context:
        last_result = execution_vote_state.get("last_result")
        if not last_result:
            return redirect(url_for("player_page"))

        vote_context = {
            "vote_id": last_result.get("vote_id", 0),
            "nominator_name": last_result.get("nominator_name") or "Nieznany",
            "nominator_seat": last_result.get("nominator_seat"),
            "nominee_name": last_result.get("nominee_name") or "Nieznany",
            "nominee_client_id": None,
            "can_vote": False,
            "has_voted": True,
            "required_votes_cast": last_result.get("required_votes_total", 0),
            "required_votes_total": last_result.get("required_votes_total", 0),
            "yes_votes": last_result.get("yes_votes", 0),
            "no_votes": last_result.get("no_votes", 0),
        }

        return render_template(
            "execution_vote.html",
            client_id=client_id,
            vote_context=vote_context,
            vote_result=last_result,
            vote_closed=True,
            error=(request.args.get("error") or "").strip(),
            submitted=request.args.get("submitted") == "1",
        )

    return render_template(
        "execution_vote.html",
        client_id=client_id,
        vote_context=vote_context,
        vote_result=None,
        vote_closed=False,
        error=(request.args.get("error") or "").strip(),
        submitted=request.args.get("submitted") == "1",
    )


@app.route("/imp-akcja", methods=["GET", "POST"])
def imp_action_page():
    client_id = session.get("client_id")
    if not client_id or client_id not in db_players:
        return redirect(url_for("index"))

    if not db_game_selection:
        return redirect(url_for("player_page"))

    if execution_vote_state["active"]:
        return redirect(url_for("execution_vote_page"))

    ensure_player_flags(db_players[client_id])
    real_character, visible_character = get_player_character_views(client_id)
    if not real_character or real_character.get("name") != "Imp":
        return redirect(url_for("player_page"))

    if db_game.get("mode") != "night":
        return redirect(url_for("player_page"))

    error = ""
    result_message = ""

    if request.method == "POST":
        target_client_id = (request.form.get("target_client_id") or "").strip()
        error, result_message = perform_imp_night_action(client_id, target_client_id)
        if not error:
            return redirect(url_for("imp_action_page", saved="1", message=result_message))

    if request.args.get("saved") == "1" and not error:
        result_message = (request.args.get("message") or "").strip()

    return render_template(
        "imp_action.html",
        candidates=get_sorted_player_options(),
        is_executed=db_players[client_id]["executed"],
        used_night=db_game.get("imp_action_done_night", False),
        status_text=get_stable_player_status(visible_character),
        error=error,
        saved=request.args.get("saved") == "1",
        result_message=result_message,
    )


@app.route("/truciciel-akcja", methods=["GET", "POST"])
def truciciel_action_page():
    client_id = session.get("client_id")
    if not client_id or client_id not in db_players:
        return redirect(url_for("index"))

    if not db_game_selection:
        return redirect(url_for("player_page"))

    if execution_vote_state["active"]:
        return redirect(url_for("execution_vote_page"))

    ensure_player_flags(db_players[client_id])
    real_character, visible_character = get_player_character_views(client_id)
    if not real_character or real_character.get("name") != "Truciciel":
        return redirect(url_for("player_page"))

    if db_game.get("mode") != "night":
        return redirect(url_for("player_page"))

    error = ""

    if request.method == "POST":
        target_client_id = (request.form.get("target_client_id") or "").strip()
        error, _ = perform_truciciel_night_action(client_id, target_client_id)
        if not error:
            socketio.emit("force_player_page_refresh", {})
            return redirect(url_for("truciciel_action_page", saved="1"))

    day_number = db_game.get("day_number", 1)
    used_today = db_game.get("truciciel_action_done_night", False)

    return render_template(
        "truciciel_action.html",
        day_number=day_number,
        candidates=get_sorted_player_options(),
        is_executed=db_players[client_id]["executed"],
        used_today=used_today,
        status_text=get_stable_player_status(visible_character),
        error=error,
        saved=request.args.get("saved") == "1",
    )


@app.route("/jasnowidz-akcja", methods=["GET", "POST"])
def jasnowidz_action_page():
    client_id = session.get("client_id")
    if not client_id or client_id not in db_players:
        return redirect(url_for("index"))

    if not db_game_selection:
        return redirect(url_for("player_page"))

    if execution_vote_state["active"]:
        return redirect(url_for("execution_vote_page"))

    ensure_player_flags(db_players[client_id])
    real_character, visible_character = get_player_character_views(client_id)
    if not real_character or real_character.get("name") != "Jasnowidz":
        return redirect(url_for("player_page"))

    if db_game.get("mode") != "day":
        return redirect(url_for("player_page"))

    error = ""

    if request.method == "POST":
        first_target_client_id = (request.form.get("first_target_client_id") or "").strip()
        second_target_client_id = (request.form.get("second_target_client_id") or "").strip()
        error, _ = perform_jasnowidz_day_action(client_id, first_target_client_id, second_target_client_id)
        if not error:
            socketio.emit("force_player_page_refresh", {})
            return redirect(url_for("jasnowidz_action_page", saved="1"))

    day_number = db_game.get("day_number", 1)
    used_today = real_character.get("jasnowidz_last_day_used") == day_number

    return render_template(
        "jasnowidz_action.html",
        day_number=day_number,
        candidates=get_sorted_player_options(),
        is_executed=db_players[client_id]["executed"],
        used_today=used_today,
        status_text=get_stable_player_status(visible_character),
        error=error,
        saved=request.args.get("saved") == "1",
    )


@app.route("/menu-koniec-gry")
def menu_koniec_gry():
    client_id = session.get("client_id")
    if not client_id:
        return redirect(url_for("index"))

    winner = db_game.get("winner")
    winner_label = ""
    message = ""

    if winner == "good":
        winner_label = "Mieszkańcy + Outsiderzy"
        message = "Gra się zakończyła. Imp został wyeliminowany."
    elif winner == "evil":
        winner_label = "Minionki + Demon"
        message = "Gra się zakończyła. Wygrywają Źli (Minionki + Demon)."
    else:
        message = "Gra jeszcze się nie zakończyła."

    return render_template(
        "menu_koniec_gry.html",
        winner=winner,
        winner_label=winner_label,
        message=message,
    )


@app.route("/reset-game-and-go-index", methods=["POST"])
def reset_game_and_go_index():
    redirect_url = url_for("index")
    socketio.emit("redirect_user", {"url": redirect_url})

    reset_all_game_state()
    session.pop("client_id", None)
    session.pop("room", None)
    return redirect(redirect_url)
    
def update_player(client_id):  
    if not db_game_selection:
        return redirect(url_for("index"))

    real_character, visible_character = get_player_character_views(client_id)
    if not visible_character:
        return redirect(url_for("index"))

    if real_character and real_character.get("name") == "Pijak":
        print(
            "[update_player] Emit masked role for Drunk "
            f"client_id={client_id}, visible_role={visible_character.get('name')}"
        )

    emit("update_player_status", {
        "player_status": get_stable_player_status(visible_character),
        "player_info": visible_character["player_info"],
        "player_image": f"/static/images/{visible_character['file']}",
        "player_link": url_for("postac", route=visible_character["route"], back="player_page")
    }, to=db_players[client_id].sid)


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)
