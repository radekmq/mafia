# -*- coding: utf-8 -*-
"""Flask application entrypoint for the Mafia game."""

import json
import logging
from uuid import uuid4

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from characters.characters_data import CHARACTERS_BY_TYPE, DB_CHARACTERS
from logger import IgnoreApiState, log_info
from player import Player, PlayerStatus, PlayerVoteStatus
from state_machine import CLOCKTOWER_GAME
from utils import require_state, user_in_play
from utils_render import (
    render_day_discussion_page,
    render_execution_page,
    render_game_over_page,
    render_inactive_page,
    render_nomination_page,
    render_voting_page,
)

# Configuration
app = Flask(__name__)
app.secret_key = "tajny_klucz"
log = logging.getLogger("werkzeug")
log.addFilter(IgnoreApiState())


@app.route("/")
def index():
    """Handle index."""
    client_id = session.get("client_id")
    log_info("Render index")
    # Jeżeli session ID istnieje w bazie graczy przekieruj do lobby
    if client_id and any(
        player.client_id == client_id for player in CLOCKTOWER_GAME.game_state.players
    ):
        log_info("client_id exists, redirect to lobby.")
        return redirect(url_for("state_lobby"))
    return render_template("index.html")


@app.route("/save-player", methods=["POST"])
def save_player():
    """Handle save player."""
    data = request.json

    # --- Pobranie danych ---
    name = data.get("name")
    numer_miejsca = data.get("numer_miejsca")
    moderator = data.get("moderator")
    password = data.get("password")
    is_admin = False

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
    if numer_miejsca in [
        player.seat_no for player in CLOCKTOWER_GAME.game_state.players
    ]:
        return jsonify({"error": "Miejsce jest już zajęte. Wybierz inne miejsce."}), 400
    if name.lower() in [
        player.name.lower() for player in CLOCKTOWER_GAME.game_state.players
    ]:
        return (
            jsonify({"error": "Nazwa gracza jest już zajęta. Wybierz inną nazwę."}),
            400,
        )
    if moderator and password == "secret":
        is_admin = True

    session["client_id"] = str(uuid4())
    client_id = session.get("client_id")
    player = Player(
        client_id=client_id, seat_no=numer_miejsca, name=name, is_admin=is_admin
    )
    CLOCKTOWER_GAME.game_state.players.append(player)

    log_info(f"Saved player: {name}, seat: {numer_miejsca}")
    if is_admin:
        log_info(f"Player {name} is admin.")
    return CLOCKTOWER_GAME.page_configuration()


@app.route("/api/state")
def api_state():
    """Handle api state."""
    return CLOCKTOWER_GAME.page_configuration()


@app.route("/lobby")
@require_state("lobby")
@user_in_play
def state_lobby():
    """Handle state lobby."""
    log_info("Render: /lobby")
    client_id = session.get("client_id")
    player = CLOCKTOWER_GAME.game_state.get_player_by_client_id(client_id)

    return render_template(
        "lobby.html",
        no_of_players=len(CLOCKTOWER_GAME.game_state.players),
        player_name=player.name,
        player_seat=player.seat_no,
        is_admin=player.is_admin,
        game_state=CLOCKTOWER_GAME.state,
    )


@app.route("/leave_game")
def leave_game():
    """Handle leave game."""
    client_id = session.get("client_id")
    if client_id:
        CLOCKTOWER_GAME.game_state.players = [
            player
            for player in CLOCKTOWER_GAME.game_state.players
            if player.client_id != client_id
        ]
        session.pop("client_id", None)
        log_info(f"Player left the game: {client_id}")
    return redirect(url_for("index"))


@app.route("/wiki")
def wiki():
    """Handle wiki."""
    session.get("client_id")
    log_info("Render: /wiki")

    return render_template(
        "wiki.html",
        back_url=url_for(f"state_{CLOCKTOWER_GAME.state}"),
        characters=CHARACTERS_BY_TYPE,
        game_state=CLOCKTOWER_GAME.state,
    )


@app.route("/wiki/<character_route>")
def wiki_character(character_route):
    """Handle wiki character."""
    session.get("client_id")
    log_info(f"Render: /wiki/{character_route}")
    character = next(
        (char for char in DB_CHARACTERS.values() if char.route == character_route), None
    )
    log_info(f"Character found for route '{character_route}': {character}")
    if not character:
        return redirect(url_for("wiki"))

    return render_template(
        f"characters/{character_route}/wiki.html",
        character=character,
        back_url=url_for("wiki"),
    )


@app.route("/game_ongoing")
def game_ongoing():
    """Handle game ongoing."""
    log_info("Render: /game_ongoing")
    return render_template("game_ongoing.html")


@app.route("/start_game", methods=["GET", "POST"])
@require_state("lobby")
@user_in_play
def start_game():
    """Handle start game."""
    # Metoda jest dynamicznie dodawana przez transitions.Machine.
    # pylint: disable=no-member
    CLOCKTOWER_GAME.start_introduction()
    if request.method == "POST":
        return jsonify({"status": "ok"}), 200
    return redirect(url_for("state_players_introduction"))


@app.route("/players_introduction")
@require_state(["players_introduction", "night_summary"])
@user_in_play
def state_players_introduction():
    """Handle state players introduction."""
    log_info("Render: /players_introduction")
    client_id = session.get("client_id")
    player = CLOCKTOWER_GAME.game_state.get_player_by_client_id(client_id)

    if not player.character:
        log_info("Player without character in player_introduction, reject player!")
        return redirect(url_for("game_ongoing"))
    
    ret_status = CLOCKTOWER_GAME.game_state.get_current_player().character.ability.effect_introduction(
        CLOCKTOWER_GAME
    )

    return ret_status


@app.route("/night_selection", methods=["POST"])
@require_state(["night_minion_action", "night_all_players_action"])
@user_in_play
def night_selection():
    log_info("Handle: night_selection")

    ret_status = CLOCKTOWER_GAME.game_state.get_current_player().character.ability.callback_night(
        CLOCKTOWER_GAME, request.form
    )

    return ret_status


@app.route("/night_demon_replace", methods=["POST"])
@require_state(["night_all_players_action"])
@user_in_play
def night_demon_replace():
    log_info("Handle: night_demon_replace")

    ret_status = CLOCKTOWER_GAME.game_state.get_current_player().character.ability.callback_night(
        CLOCKTOWER_GAME, request.form, replace_demon=True
    )

    return ret_status


@app.route("/night_minion_action")
@require_state("night_minion_action")
@user_in_play
def state_night_minion_action():
    """Handle state night minion action."""
    log_info("Render: /night_minion_action")
    if CLOCKTOWER_GAME.game_state.get_current_player().alive == PlayerStatus.DEAD:
        log_info(
            "Current player is dead during night_minion_action, render inactive page."
        )
        return render_inactive_page(CLOCKTOWER_GAME)
    return CLOCKTOWER_GAME.game_state.get_current_player().character.ability.effect_night_minion(
        CLOCKTOWER_GAME
    )


@app.route("/night_all_players_action")
@require_state("night_all_players_action")
@user_in_play
def state_night_all_players_action():
    """Handle state night all players action."""
    log_info("Render: /night_all_players_action")
    if CLOCKTOWER_GAME.game_state.get_current_player().alive == PlayerStatus.DEAD:
        log_info(
            "Current player is dead during night_all_players_action, render inactive page."
        )
        return render_inactive_page(CLOCKTOWER_GAME)
    return CLOCKTOWER_GAME.game_state.get_current_player().character.ability.effect_night_all_players(
        CLOCKTOWER_GAME
    )


@app.route("/day_discussions")
@require_state("day_discussions")
@user_in_play
def state_day_discussions():
    """Handle state day discussions."""
    log_info("Render: /day_discussions")
    return render_day_discussion_page(CLOCKTOWER_GAME)


@app.route("/nomination")
@require_state("nomination")
@user_in_play
def state_nomination():
    """Handle state nomination."""
    log_info("Render: /nomination")
    return render_nomination_page(CLOCKTOWER_GAME)


@app.route("/nominate_execute", methods=["POST"])
@require_state(["nomination"])
@user_in_play
def nominate_execute():
    log_info("Handle: nominate_execute")
    data = request.form
    try:
        selected_json = json.loads(data.get("selected_json", "[]"))
    except json.JSONDecodeError:
        selected_json = []

    if not selected_json:
        log_info("No player selected in Imp's ability callback.")
        return redirect(url_for("state_nomination"))

    log_info(f"Selected player client_id for nomination: {selected_json[0]}")

    player_selected = CLOCKTOWER_GAME.game_state.get_player_by_client_id(
        selected_json[0]
    )
    if not player_selected:
        log_info(f"No player found for nominated client_id: {selected_json[0]}")
        return redirect(url_for("state_nomination"))

    log_info(
        f"Player selected for nomination: {player_selected.name} (client_id: {player_selected.client_id})"
    )

    CLOCKTOWER_GAME.voting_system.append_nominated_player(player_selected)
    current_player = CLOCKTOWER_GAME.game_state.get_current_player()
    CLOCKTOWER_GAME.voting_system.set_nominator(
        current_player, CLOCKTOWER_GAME.game_state.players
    )  # Ustawienie nominatora i kolejności głosowania
    CLOCKTOWER_GAME.nomination_finished()  # Przejście do fazy głosowania

    return redirect(url_for("state_voting"))


@app.route("/voting")
@require_state("voting")
@user_in_play
def state_voting():
    """Handle state voting."""
    log_info("Render: /voting")
    return render_voting_page(CLOCKTOWER_GAME)


@app.route("/vote_execute", methods=["POST"])
@require_state(["voting"])
@user_in_play
def vote_execute():
    log_info("Handle: vote_execute")
    data = request.form
    try:
        selected_json = json.loads(data.get("selected_json", "[]"))
    except json.JSONDecodeError:
        selected_json = []

    if not selected_json:
        log_info("No player selected in Imp's ability callback.")
        return redirect(url_for("state_voting"))

    yes_no_vote = bool(selected_json[0])
    current_player = CLOCKTOWER_GAME.game_state.get_current_player()

    if yes_no_vote:
        log_info(f"Player {current_player.name} voted YES for the nominee.")
        current_player.set_vote_status(PlayerVoteStatus.VOTED_YES)
        CLOCKTOWER_GAME.voting_system.vote_for_active_nominee(current_player)
    else:
        log_info(f"Player {current_player.name} refused to vote for the nominee.")
        current_player.set_vote_status(PlayerVoteStatus.VOTED_NO)

    if not CLOCKTOWER_GAME.voting_system.apply_next_voter():
        log_info("All voters have voted, redirecting to nomination results.")
        CLOCKTOWER_GAME.voting_finished()

    return redirect(url_for("state_voting"))


# Finish with nomination -> voting, then enter execution phase
@app.route("/complete_nomination", methods=["POST"])
@user_in_play
def complete_nomination():
    """Handle complete nomination."""
    log_info("Handle: complete_nomination")
    CLOCKTOWER_GAME.start_execution_phase()
    return jsonify({"status": "ok"}), 200


@app.route("/execution")
@require_state("execution")
@user_in_play
def state_execution():
    """Handle state execution."""
    log_info("Render: /execution")
    return render_execution_page(CLOCKTOWER_GAME)


@app.route("/game_over")
@require_state("game_over")
@user_in_play
def state_game_over():
    """Handle state game over."""
    log_info("Render: /game_over")
    return render_game_over_page(CLOCKTOWER_GAME)


@app.route("/next_state", methods=["POST"])
@user_in_play
def state_next_state():
    """Handle state next state."""

    if CLOCKTOWER_GAME.state == "players_introduction":
        log_info("Transition from players_introduction to night_minion_action")
        CLOCKTOWER_GAME.start_evil_night_actions()

    elif CLOCKTOWER_GAME.state == "night_minion_action":
        log_info("Transition from night_minion_action to night_all_players_action")
        CLOCKTOWER_GAME.start_all_players_night_actions()

    elif CLOCKTOWER_GAME.state == "night_all_players_action":
        log_info("Transition from night_all_players_action to day_discussions")
        CLOCKTOWER_GAME.all_night_actions_done()

    elif CLOCKTOWER_GAME.state == "night_summary":
        log_info("Transition from night_summary to day_discussions")
        CLOCKTOWER_GAME.start_day_discussions()

    elif CLOCKTOWER_GAME.state == "day_discussions":
        log_info("Transition from day_discussions to nomination")
        CLOCKTOWER_GAME.start_nomination_phase()

    elif CLOCKTOWER_GAME.state == "nomination":
        log_info("Transition from nomination to voting")
        CLOCKTOWER_GAME.nomination_finished()

    elif CLOCKTOWER_GAME.state == "voting":
        log_info("Transition from voting to nomination")
        CLOCKTOWER_GAME.voting_finished()

    elif CLOCKTOWER_GAME.state == "execution":
        log_info("Transition from execution to night_minion_action")
        CLOCKTOWER_GAME.execution_finished()

    elif CLOCKTOWER_GAME.state == "game_over":
        log_info("Transition from game_over to lobby")
        CLOCKTOWER_GAME.finish_game()

    else:
        log_info(f"Invalid state for next_state transition: {CLOCKTOWER_GAME.state}")
        return jsonify({"status": "error", "message": "Nieprawidłowy stan gry"}), 400

    return jsonify({"status": "ok"}), 200


@app.route("/confirm_admin_action")
@require_state(["night_all_players_action"])
@user_in_play
def confirm_admin_action():
    """Handle confirm admin action."""
    client_id = session.get("client_id")
    player = CLOCKTOWER_GAME.game_state.get_player_by_client_id(client_id)
    if player:
        player.confirm_admin_action()
        log_info(f"Player {player.name} confirmed admin action.")
    return redirect(url_for("state_night_all_players_action"))


@app.route("/confirm_minion_action")
@require_state(["night_minion_action"])
@user_in_play
def confirm_minion_action():
    """Handle confirm minion action."""
    client_id = session.get("client_id")
    player = CLOCKTOWER_GAME.game_state.get_player_by_client_id(client_id)
    if player:
        player.confirm_minion_action()
        log_info(f"Player {player.name} confirmed minion action.")
    return redirect(url_for("state_night_minion_action"))


@app.route("/night_summary")
@require_state("night_summary")
@user_in_play
def state_night_summary():
    """Handle state night presentations."""
    log_info("Render: /night_summary")

    return redirect(url_for("state_players_introduction"))


# =========================
# INICJALIZACJA
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
