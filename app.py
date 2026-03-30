# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
from flask_socketio import SocketIO, join_room, leave_room, emit
from uuid import uuid4
from utils import Database, assign_players_to_characters, fun_praczka
import random

from database import db_characters, trouble_brewing_setup

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
    "no_of_players": 0,
    "admin_id": None,
    "players": []
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
    "nominator_client_id": None,
    "nominee_client_id": None,
    "nominee_name": None,
    "votes": {},
    "required_voters": [],
    "optional_voters": [],
}

ALLOWED_BACK_ENDPOINTS = {"lobby", "handle_menu", "index"}


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


def is_seat_taken(seat, excluded_client_id=None):
    for existing_client_id, player in db_players.get_all().items():
        if existing_client_id == excluded_client_id:
            continue
        if player.get("seat") == seat:
            return True

    return False


def build_game_status_payload():
    return {
        "no_of_players": len(db_players),
        "game_status": db_game["game_active"],
        "game_active": db_game["game_active"],
        "char_presented": db_game["char_presented"],
        "mode": db_game["mode"],
    }


def reset_execution_vote_state():
    execution_vote_state["active"] = False
    execution_vote_state["nominator_client_id"] = None
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
        db_players[nominee_client_id]["executed"] = True
        player_executed = True

    if player_executed:
        message = f"Gracz {nominee_name} został wyeliminowany z gry."
    else:
        message = f"Gracz {nominee_name} nie został wyeliminowany (większość NIE lub remis)."

    emit_execution_vote_result(message, yes_votes, no_votes, player_executed)
    reset_execution_vote_state()


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

    if not client_id or client_id not in db_players:
        emit("nomination_candidates", {"error": "Nie znaleziono gracza."})
        return

    ensure_player_flags(db_players[client_id])
    if db_players[client_id]["executed"]:
        emit("nomination_candidates", {"error": "Gracz wyeliminowany nie może nominować."})
        return

    if execution_vote_state["active"]:
        emit("nomination_candidates", {"error": "Trwa już inne głosowanie."})
        return

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

    emit("nomination_candidates", {"players": candidates})


@socketio.on("start_execution_vote")
def handle_start_execution_vote(data):
    nominator_client_id = data.get("clientId") or data.get("client_id")
    nominee_client_id = data.get("nominee_client_id")

    if execution_vote_state["active"]:
        emit("execution_vote_error", {"error": "Trwa już inne głosowanie."})
        return

    if not nominator_client_id or nominator_client_id not in db_players:
        emit("execution_vote_error", {"error": "Nie znaleziono nominującego gracza."})
        return

    ensure_player_flags(db_players[nominator_client_id])
    if db_players[nominator_client_id]["executed"]:
        emit("execution_vote_error", {"error": "Gracz wyeliminowany nie może nominować."})
        return

    if not nominee_client_id or nominee_client_id not in db_players:
        emit("execution_vote_error", {"error": "Nie znaleziono nominowanego gracza."})
        return

    ensure_player_flags(db_players[nominee_client_id])
    if db_players[nominee_client_id]["executed"]:
        emit("execution_vote_error", {"error": "Nie można nominować gracza już wyeliminowanego."})
        return

    execution_vote_state["active"] = True
    execution_vote_state["nominator_client_id"] = nominator_client_id
    execution_vote_state["nominee_client_id"] = nominee_client_id
    execution_vote_state["nominee_name"] = db_players[nominee_client_id].get("name", "Nieznany")
    execution_vote_state["votes"] = {}
    execution_vote_state["required_voters"] = get_alive_player_ids()
    execution_vote_state["optional_voters"] = get_optional_dead_voter_ids()

    emit_execution_vote_started()


@socketio.on("cast_execution_vote")
def handle_cast_execution_vote(data):
    voter_client_id = data.get("clientId") or data.get("client_id")
    raw_vote = str(data.get("vote", "")).strip().lower()

    if raw_vote in {"tak", "yes", "true", "1"}:
        vote = "yes"
    elif raw_vote in {"nie", "no", "false", "0"}:
        vote = "no"
    else:
        emit("execution_vote_error", {"error": "Niepoprawny głos. Użyj TAK lub NIE."})
        return

    if not execution_vote_state["active"]:
        emit("execution_vote_error", {"error": "Aktualnie nie trwa żadne głosowanie."})
        return

    if not voter_client_id or voter_client_id not in db_players:
        emit("execution_vote_error", {"error": "Nie znaleziono gracza głosującego."})
        return

    if voter_client_id in execution_vote_state["votes"]:
        emit("execution_vote_error", {"error": "Ten gracz już oddał głos."})
        return

    required_voters = set(execution_vote_state["required_voters"])
    optional_voters = set(execution_vote_state["optional_voters"])

    if voter_client_id not in required_voters and voter_client_id not in optional_voters:
        emit("execution_vote_error", {"error": "Ten gracz nie może oddać głosu w tym głosowaniu."})
        return

    ensure_player_flags(db_players[voter_client_id])
    if voter_client_id in optional_voters:
        db_players[voter_client_id]["vote_dead"] = False

    execution_vote_state["votes"][voter_client_id] = vote
    finalize_execution_vote_if_ready()
        
@app.route("/")
def index():
    client_id = session.get("client_id")
    if client_id and client_id in db_players:
        return render_template(
            "index.html",
            name=db_players[client_id]["name"],
            character=db_players[client_id]["character"],
            numer_miejsca=db_players[client_id].get("seat", ""),
        )
    else:
        return render_template("index.html", name="", character="", numer_miejsca="")

@app.route("/save-player", methods=["POST"])
def save_player():
    data = request.get_json()
    name = data.get("name")
    character = data.get("character")
    raw_seat = data.get("numer_miejsca")
    client_id = data.get("clientId") or data.get("client_id")
    socket_sid = data.get("socketSid")
    session["client_id"] = client_id
    is_admin_login = name == "admin" and character == "secret"
    print(f"Save {name=}, {character=}, {raw_seat=}, {client_id=}, {socket_sid=}")
    
    if client_id:
        if not name or not character:
            return jsonify({"error": "Brak wymaganych danych"}), 400

        seat = None
        if not is_admin_login:
            try:
                seat = parse_seat(raw_seat)
            except ValueError as exc:
                return jsonify({"error": str(exc)}), 400

            if is_seat_taken(seat, excluded_client_id=client_id):
                return jsonify({"error": f"Miejsce numer {seat} jest już zajęte"}), 400
        
        if is_admin_login:
            db_game["admin_id"] = client_id
            seed_default_players_for_admin()
            db_game["no_of_players"] = len(db_players)
            socketio.emit("update_game_status", build_game_status_payload())
            
            return redirect(url_for("handle_menu"))
        
        if client_id not in db_players:
            print(f"Dodaje nowego gracza: {name}, postać: {character}, seat: {seat}")
            db_players.add(client_id, { "name" : None, "character" : None, "seat": None, "executed": False, "vote_dead": True, "sid": None} )

        db_players[client_id]["name"] = name
        db_players[client_id]["character"] = character
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

    return jsonify({
        "no_of_players": len(db_players),
        "game_active": db_game["game_active"],
        "char_presented": db_game["char_presented"],
        "mode": db_game["mode"],
        "is_player": is_player,
    }), 200

@app.route("/menu")
def handle_menu():
    client_id = session.get("client_id")
    if(client_id != db_game["admin_id"]):
        return redirect(url_for("index"))
    
    return render_template(
        "menu.html",
        liczba_graczy=len(db_players),
        char_presented=db_game["char_presented"],
        current_mode=db_game["mode"],
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

    if previous_mode == "day" and mode == "night" and db_game_selection:
        for characters in db_game_selection.values():
            for character in characters:
                if character.get("name") == "Empata":
                    character.pop("resolved_player_status", None)

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
            
            socketio.emit("update_game_status", { 
                                                "no_of_players": db_game["no_of_players"], 
                                                "game_status": "Gra przygotowana, oczekuj na losowanie postaci.",
                                                "game_active": db_game["game_active"],
                                                "char_presented": db_game["char_presented"],
                                                "mode": db_game["mode"],
                                                })
        elif event == "show":
            print(f"[create] Otrzymano żądanie losowania postaci od client_id={client_id}")
            if len(db_players) < 5:
                return jsonify({"error": "Too few players. Minimum is 5"}), 404

            db_game["char_presented"] = True
            db_game["no_of_players"] = len(db_players)
            socketio.emit("update_game_status", { 
                                                "no_of_players": db_game["no_of_players"], 
                                                "game_status": "Postacie zostały rozlosowane.",
                                                "game_active": db_game["game_active"],
                                                "char_presented": db_game["char_presented"],
                                                "mode": db_game["mode"],
                                                })
            
            print("\n\n")
            global db_game_selection
            db_game_selection = assign_players_to_characters(
                db_players.get_all_client_ids(),
                trouble_brewing_setup,
                db_characters,
                db_players.get_all(),
            )
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
    # Status losowany raz na postac i trzymany do kolejnego losowania postaci.
    if "resolved_player_status" in character:
        return character["resolved_player_status"]

    player_status_field = character.get("player_status")
    if callable(player_status_field):
        resolved_status = player_status_field(db_game_selection, db_players)
    elif isinstance(player_status_field, str):
        resolved_status = player_status_field
    else:
        resolved_status = "Brak informacji o statusie postaci."

    character["resolved_player_status"] = resolved_status
    return resolved_status


def redirect_players_to_character_pages():
    player_page_url = url_for("player_page")
    target_client_ids = db_players.get_all_client_ids()

    for client_id in target_client_ids:
        player = db_players[client_id]
        print(f"[redirect_players_to_character_pages] Przetwarzam client_id={client_id}, player={player}")
        print(f"[redirect_players_to_character_pages] player.name={player.get('name')}, player.character={player.get('character')}, player.sid={player.get('sid')}")
        sid = player.get("sid")

        if not sid:
            print(f"[redirect_players_to_character_pages] Pomijam client_id={client_id}, brak aktywnego sid")
            continue

        socketio.emit("redirect_user", {"url": player_page_url}, to=sid)

    # Fallback dla klientów mobilnych/przeglądarek, gdzie mapowanie client_id -> sid
    # mogło nie zsynchronizować się na czas; klient sam sprawdza czy jego client_id jest na liście.
    socketio.emit(
        "redirect_user_for_clients",
        {"url": player_page_url, "target_client_ids": target_client_ids},
    )


@app.route("/player_page")
def player_page():
    client_id = session.get("client_id")
    if client_id == None: 
        return redirect(url_for("index"))
    if not db_game_selection:
        return redirect(url_for("index"))
    
    real_character, visible_character = get_player_character_views(client_id)
    if not visible_character:
        abort(404, description=f"Brak postaci o client_id={client_id}")

    player_status = get_stable_player_status(visible_character)
    player_info = visible_character["player_info"]
    player_image = f"/static/images/{visible_character['file']}"
    player_link = f"/player/{client_id}"
    ensure_player_flags(db_players[client_id])

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
    )
    
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
        "player_link": f"/player/{client_id}"
    }, to=db_players[client_id].sid)


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)
