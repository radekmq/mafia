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
    "no_of_players": 0,
    "admin_id": None,
    "players": []
}
db_game_selection = None

@socketio.on('connect')
def handle_connect():
    sid = request.sid
    print(f"Nowe połączenie: {sid}")

@socketio.on('client_id_response')
def handle_client_id(data):
    sid = request.sid
    client_id = data.get("client_id")

    print(f"Otrzymano client_id={client_id} dla sid={sid}")
    # Jeśli gracz już istnieje po client_id, aktualizujemy SID
    if client_id in db_players:
        print("Znaleziono istniejącego gracza, aktualizuję SID...")
        player = db_players[client_id]
        player["sid"] = sid

@socketio.on("disconnect")
def handle_disconnect():
    print(f"🔴 Rozłączono: {request.sid}")
        
@app.route("/")
def index():
    client_id = session.get("client_id")
    if client_id and client_id in db_players:
        return render_template("index.html", name=db_players[client_id]["name"], character=db_players[client_id]["character"])
    else:
        return render_template("index.html", name="", character="")

@app.route("/save-player", methods=["POST"])
def save_player():
    data = request.get_json()
    name = data.get("name")
    character = data.get("character")
    client_id = data.get("clientId")
    session["client_id"] = client_id
    print(f"Save {name=}, {character=}, {client_id=}")
    
    if client_id:
        if not name or not character:
            return jsonify({"error": "Brak wymaganych danych"}), 400
        
        if name=="admin" and character=="secret":
            db_game["admin_id"] = client_id
            
            return redirect(url_for("handle_menu"))
        
        if client_id not in db_players:
            print(f"Dodaje nowego gracza: {name}, postać: {character}")
            db_players.add(client_id, { "name" : None, "character" : None, "sid": None} )
            db_players[client_id]["name"] = name
            db_players[client_id]["character"] = character
        
        socketio.emit("update_game_status", { "no_of_players": len(db_players), "game_status": db_game["game_active"] })
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

@app.route("/menu")
def handle_menu():
    client_id = session.get("client_id")
    if(client_id != db_game["admin_id"]):
        return redirect(url_for("index"))
    
    return render_template("menu.html", liczba_graczy=len(db_players), char_presented = db_game["char_presented"])
    
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
                                                })
        elif event == "show":
            if len(db_players) < 5:
                return jsonify({"error": "Too few players. Minimum is 5"}), 404

            db_game["char_presented"] = True
            db_game["no_of_players"] = len(db_players)
            socketio.emit("update_game_status", { 
                                                "no_of_players": db_game["no_of_players"], 
                                                "game_status": "Postacie zostały rozlosowane.",
                                                "game_active": db_game["game_active"],
                                                "char_presented": db_game["char_presented"],
                                                })
            
            print("\n\n")
            global db_game_selection
            db_game_selection = assign_players_to_characters(db_players.get_all_client_ids(), trouble_brewing_setup, db_characters)
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
        
        if client_id in db_players:
            db_players.remove(client_id)
            print(f"[leave_game] Gracz {client_id} usunięty. Pozostali: {db_players.get_all()}")
        else:
            print(f"[leave_game] Gracza {client_id} nie było w pokoju!")
            return redirect(url_for("index"))
        
        if client_id in db_game["players"]:
            db_game["players"].remove(client_id)
        
        return redirect(url_for("index"))
    
@app.route("/postac/<route>")
def postac(route):
    for kategoria, postaci in db_characters.items():
        for p in postaci:
            if p["route"] == route:
                return render_template(f"characters/{route}.html", character=p)
    abort(404)

@app.route("/wiki")
def handle_wiki():
    return render_template("wiki.html", characters=db_characters)


def find_character_by_client_id(client_id, db_characters):
    for group_name, characters in db_characters.items():
        for char in characters:
            if char.get("client_id") == client_id:
                return char
    return None


def redirect_players_to_character_pages():
    player_page_url = url_for("player_page")

    for client_id in db_players.get_all_client_ids():
        player = db_players[client_id]
        sid = player.get("sid")

        if not sid:
            print(f"[redirect_players_to_character_pages] Pomijam client_id={client_id}, brak aktywnego sid")
            continue

        socketio.emit("redirect_user", {"url": player_page_url}, to=sid)


@app.route("/player_page")
def player_page():
    client_id = session.get("client_id")
    if client_id == None: 
        return redirect(url_for("index"))
    
    character = find_character_by_client_id(client_id, db_game_selection)
    if not character:
        abort(404, description=f"Brak postaci o client_id={client_id}")

    player_status = character["player_status"](db_characters, db_players, False)
    player_info = character["player_info"]
    player_image = f"/static/images/{character['file']}"
    player_link = f"/player/{client_id}"

    return render_template(
        "player_page.html",
        client_id=client_id,
        player_status=player_status,
        player_info=player_info,
        player_image=player_image,
        player_link=player_link
    )
    
def update_player(client_id):  
    character = find_character_by_client_id(client_id, db_characters)
    if not character:
        return redirect(url_for("index"))

    emit("update_player_status", {
        "player_status": character["player_status"](),
        "player_info": character["player_info"],
        "player_image": f"/static/images/{character['file']}",
        "player_link": f"/player/{character['client_id']}"
    }, to=db_players[client_id].sid)


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)
