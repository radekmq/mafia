# -*- coding: utf-8 -*-
"""Flask application entrypoint for the Mafia game."""

import logging

import eventlet

eventlet.monkey_patch()

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_socketio import SocketIO

from game_engine import GameEngine
from game_events import Event
from logger import log_info

# Configuration
app = Flask(__name__, static_folder="static")
app.secret_key = "tajny_klucz"
app.engine = GameEngine()
log = logging.getLogger("werkzeug")

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="eventlet",
    logger=True,
    engineio_logger=True,
)

app.engine.dispatcher.register_socketio(socketio)


# =========================
# 🔌 SOCKET CONNECT
# =========================
@socketio.on("connect")
def on_connect():
    log_info(">>> CLIENT CONNECTED: %s", request.sid)
    if app.engine.game_state.if_player_exist(session.get("client_id")):
        event = Event(
            name="player_connected",
            actor_id=session.get("client_id"),
            priority=50,
            data={"socket_id": request.sid},
        )
        app.engine.enqueue_event(event)
    else:
        log_info(">>> CLIENT NOT FOUND IN GAME: %s", session.get("client_id"))


@socketio.on("disconnect")
def handle_disconnect():
    log_info(">>> CLIENT DISCONNECTED")


@socketio.on("message")
def handle_message(msg):
    log_info(">>> SOCKET MESSAGE: %s", msg)

    event = Event(
        name=(
            msg.get("type", "unknown_message")
            if isinstance(msg, dict)
            else "unknown_message"
        ),
        actor_id=session.get("client_id"),
        priority=50,
        data=msg,
    )
    app.engine.enqueue_event(event)


@app.route("/")
def index():
    """Handle index."""
    log_info("[app.route] Render index")
    # Jeżeli session ID istnieje w bazie graczy przekieruj do lobby
    if app.engine.game_state.if_player_exist(session.get("client_id")):
        return redirect(url_for("state_lobby"))
    return render_template("index.html")


@app.route("/save-player", methods=["POST"])
def save_player():
    """Handle save player."""
    log_info("[app.route][POST] Save player")
    if app.engine.game_state.if_player_exist(session.get("client_id")):
        return redirect(url_for("state_lobby"))

    # --- Pobranie danych ---
    data = request.json
    name = data.get("name")
    numer_miejsca = data.get("numer_miejsca")
    moderator = data.get("moderator")
    password = data.get("password")

    # --- Walidacja ---
    if not name:
        return jsonify({"error": "Brak nazwy"}), 400
    if not numer_miejsca:
        return jsonify({"error": "Brak numeru miejsca"}), 400
    if not isinstance(numer_miejsca, int) or numer_miejsca < 1:
        return (
            jsonify({"error": "Numer miejsca musi być liczbą całkowitą większą niż 0"}),
            400,
        )
    if app.engine.game_state.if_seat_occupied(numer_miejsca):
        return jsonify({"error": "Miejsce jest już zajęte. Wybierz inne miejsce."}), 400
    if app.engine.game_state.if_name_already_exist(name):
        return (
            jsonify({"error": "Nazwa gracza jest już zajęta. Wybierz inną nazwę."}),
            400,
        )

    app.engine.game_state.add_new_player(name, numer_miejsca, moderator, password)
    return redirect(url_for("state_lobby"))


@app.route("/lobby")
def state_lobby():
    """Handle state lobby."""
    log_info("[app.route] Render: /lobby")
    if app.engine.game_state.if_player_exist(session.get("client_id")):
        return render_template("game.html")
    else:
        return redirect(url_for("index"))


@app.route("/leave_game")
def leave_game():
    """Handle leave game."""
    log_info("[app.route] Render: /leave_game")

    event = Event(
        name="leave_game",
        actor_id="SYSTEM",
        priority=50,
        data={},
    )
    app.engine.enqueue_event(event)

    app.engine.game_state.remove_player(session.get("client_id"))
    session.pop("client_id", None)
    return redirect(url_for("index"))


@app.route("/wiki")
def wiki():
    """Handle wiki."""
    log_info("[app.route] Render: /wiki")
    state = app.engine.state_machine.state

    return render_template(
        "wiki.html",
        back_url=url_for("state_lobby"),
        characters=app.engine.game_setup.get_dict_of_characters(),
        game_state=state,
    )


@app.route("/wiki/<character_route>")
def wiki_character(character_route):
    """Handle wiki character."""
    log_info(f"[app.route] Render: /wiki/{character_route}")
    character = app.engine.game_setup.get_character_by_route(character_route)
    if not character:
        return redirect(url_for("wiki"))

    return render_template(
        f"characters/{character_route}/wiki.html",
        character=character,
        back_url=url_for("wiki"),
    )


# =========================
# INICJALIZACJA
# =========================

if __name__ == "__main__":
    log_info("Starting Flask application...")
    app.engine.dispatcher.start_worker()
    # app.run(host="0.0.0.0", port=5000, debug=True)
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
