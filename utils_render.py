"""Module for handling utility functions and classes in the Mafia game."""

from flask import redirect, render_template, url_for

from characters.character import RoleType
from logger import log_info
from player import PlayerStatus
from utils import get_state_description


def render_player_page(ct_game, template_name: str, data: dict):
    """Render player page based on the current game state and player status."""
    current_player = ct_game.game_state.get_current_player()
    if not current_player:
        log_info("No current player found for rendering player page.")
        return redirect(url_for("index"))

    # Default rendering if no specific character effect is defined
    return render_template(
        template_name,
        role_name=current_player.character.name,
        player_link=current_player.character.route,
        player_image=current_player.character.image_path,
        player_info=current_player.character.ability.description,
        player_name=current_player.name,
        game_state_description=get_state_description(ct_game.state),
        is_admin=current_player.is_admin,
        player_seat=current_player.seat_no,
        character_data=data,
        game_state=ct_game.state,
        is_alive=current_player.alive == PlayerStatus.ALIVE,
        player_status_list=[
            (player.name, player.alive == PlayerStatus.ALIVE)
            for player in ct_game.game_state.players
        ],
    )


def render_introduction_page(ct_game):
    """Render introduction page."""
    current_player = ct_game.game_state.get_current_player()
    if not current_player:
        log_info("No current player found for rendering player page.")
        return redirect(url_for("index"))

    return render_template(
        "player_page_night.html",
        role_name=current_player.character.name,
        player_link=current_player.character.route,
        player_image=current_player.character.image_path,
        player_info=current_player.character.ability.description,
        player_name=current_player.name,
        game_state_description=get_state_description(ct_game.state),
        is_admin=current_player.is_admin,
        player_seat=current_player.seat_no,
        game_state=ct_game.state,
        is_alive=current_player.alive == PlayerStatus.ALIVE,
        player_status_list=[
            (player.name, player.alive == PlayerStatus.ALIVE)
            for player in ct_game.game_state.players
        ],
    )


def render_inactive_page(ct_game):
    """Render inactive player page."""
    current_player = ct_game.game_state.get_current_player()
    if not current_player:
        log_info("No current player found for rendering player page.")
        return redirect(url_for("index"))

    return render_template(
        "player_page_inactive.html",
        player_name=current_player.name,
        game_state_description=get_state_description(ct_game.state),
        is_admin=current_player.is_admin,
        player_seat=current_player.seat_no,
        game_state=ct_game.state,
        is_alive=current_player.alive == PlayerStatus.ALIVE,
        player_status_list=[
            (player.name, player.alive == PlayerStatus.ALIVE)
            for player in ct_game.game_state.players
        ],
    )


def render_day_discussion_page(ct_game):
    """Render day discussion page."""
    current_player = ct_game.game_state.get_current_player()
    if not current_player:
        log_info("No current player found for rendering player page.")
        return redirect(url_for("index"))

    return render_template(
        "player_page_day_discussion.html",
        player_name=current_player.name,
        game_state_description=get_state_description(ct_game.state),
        is_admin=current_player.is_admin,
        player_seat=current_player.seat_no,
        game_state=ct_game.state,
        player_status_list=[
            (player.name, player.alive == PlayerStatus.ALIVE)
            for player in ct_game.game_state.players
        ],
        is_alive=current_player.alive == PlayerStatus.ALIVE,
    )


def render_nomination_page(ct_game):
    """Render nomination page."""
    current_player = ct_game.game_state.get_current_player()
    if not current_player:
        log_info("No current player found for rendering player page.")
        return redirect(url_for("index"))

    return render_template(
        "player_page_day_nomination.html",
        player_name=current_player.name,
        game_state_description=get_state_description(ct_game.state),
        is_admin=current_player.is_admin,
        player_seat=current_player.seat_no,
        game_state=ct_game.state,
        is_alive=current_player.alive == PlayerStatus.ALIVE,
        player_status_list=[
            (player.name, player.alive == PlayerStatus.ALIVE)
            for player in ct_game.game_state.players
        ],
    )


def render_voting_page(ct_game):
    """Render voting page."""
    current_player = ct_game.game_state.get_current_player()
    if not current_player:
        log_info("No current player found for rendering player page.")
        return redirect(url_for("index"))

    return render_template(
        "player_page_day_voting.html",
        player_name=current_player.name,
        game_state_description=get_state_description(ct_game.state),
        is_admin=current_player.is_admin,
        player_seat=current_player.seat_no,
        game_state=ct_game.state,
        is_alive=current_player.alive == PlayerStatus.ALIVE,
        player_status_list=[
            (player.name, player.alive == PlayerStatus.ALIVE)
            for player in ct_game.game_state.players
        ],
    )


def render_execution_page(ct_game):
    """Render execution page."""
    current_player = ct_game.game_state.get_current_player()
    if not current_player:
        log_info("No current player found for rendering player page.")
        return redirect(url_for("index"))

    return render_template(
        "player_page_day_execution.html",
        player_name=current_player.name,
        game_state_description=get_state_description(ct_game.state),
        is_admin=current_player.is_admin,
        player_seat=current_player.seat_no,
        game_state=ct_game.state,
        is_alive=current_player.alive == PlayerStatus.ALIVE,
        player_status_list=[
            (player.name, player.alive == PlayerStatus.ALIVE)
            for player in ct_game.game_state.players
        ],
    )


def render_game_over_page(ct_game):
    """Render game over page."""
    current_player = ct_game.game_state.get_current_player()
    if not current_player:
        log_info("No current player found for rendering player page.")
        return redirect(url_for("index"))

    is_demon_alive = any(
        player.alive == PlayerStatus.ALIVE
        and player.character.role_type == RoleType.DEMON
        for player in ct_game.game_state.players
    )

    return render_template(
        "player_page_game_over.html",
        game_winner_text="Deamon and Minions win the game!"
        if is_demon_alive
        else "Townfolks and outsiders win the game!",
        is_alive=current_player.alive == PlayerStatus.ALIVE,
        is_admin=current_player.is_admin,
    )
