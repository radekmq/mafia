"""Module for handling utility functions and classes in the Mafia game."""

from flask import redirect, render_template, url_for

from logger import log_info
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
    )
