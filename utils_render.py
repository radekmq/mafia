"""Module for handling utility functions and classes in the Mafia game."""

from flask import redirect, render_template, url_for

from characters.character import RoleType
from logger import log_info
from player import PlayerStatus, PlayerVoteStatus
from utils import get_minion_action_status, get_state_description


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
        minion_action_status=get_minion_action_status(ct_game),
        admin_confirm_status=[
            {"name": player.name, "confirmed": player.is_admin_action_confirmed()}
            for player in ct_game.game_state.players
        ]
        if ct_game.state in ["night_all_players_action"]
        else None,
        player_confirmed_action=current_player.is_admin_action_confirmed()
        if ct_game.state in ["night_all_players_action"]
        else None,
        minion_confirmed_action=current_player.is_minion_action_confirmed()
        if ct_game.state in ["night_minion_action"]
        else None,
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
        minion_action_status=get_minion_action_status(ct_game),
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

    log_info(f"Nominated players: {ct_game.voting_system.get_nominated_players()}")

    list_of_players = [
        (player.name, player.client_id)
        for player in ct_game.game_state.players
        if player.alive == PlayerStatus.ALIVE
        and not ct_game.voting_system.is_player_nominated(player.client_id)
    ]
    log_info(
        f"Alive players available for nomination: {[name for name, _ in list_of_players]}"
    )
    if not list_of_players:
        log_info("No alive players available for nomination.")
        players_available = False
    else:
        players_available = True

    return render_template(
        "player_page_day_nomination.html",
        is_admin=current_player.is_admin,
        alive_player_list=list_of_players,
        nominated_players=ct_game.voting_system.get_nominated_players_json(),
        players_available=players_available,
        game_state=ct_game.state,
    )


def render_voting_page(ct_game):
    """Render voting page."""
    current_player = ct_game.game_state.get_current_player()
    if not current_player:
        log_info("No current player found for rendering player page.")
        return redirect(url_for("index"))

    nominated_player_name = (
        ct_game.game_state.get_player_name(
            ct_game.voting_system.active_nominee_player.client_id
        )
        if ct_game.voting_system.active_nominee_player
        else None
    )

    log_info(f"player_client_id: {current_player.client_id}")
    log_info(
        f"active_voting_player_client_id: {ct_game.voting_system.get_active_voter_client_id()}"
    )

    player_vote_status = []
    for player in ct_game.game_state.players:
        status = {"name": player.name, "vote_status": player.get_vote_status().value}
        if not ct_game.voting_system.is_player_in_voting_list(player.client_id):
            log_info(f"Player {player.name} is NOT in the voting list.")
            status["vote_status"] = PlayerVoteStatus.NO_RIGHT_TO_VOTE.value
        player_vote_status.append(status)

    return render_template(
        "player_page_day_voting.html",
        is_admin=current_player.is_admin,
        nominated_player_name=nominated_player_name,
        player_client_id=current_player.client_id,
        active_voting_player_client_id=ct_game.voting_system.get_active_voter_client_id(),
        vote_submitted=ct_game.voting_system.is_vote_submitted(
            current_player.client_id
        ),
        game_state=ct_game.state,
        player_vote_status=player_vote_status,
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
        executed_player_name=ct_game.game_state.executed_player_name,
    )


def render_game_over_page(ct_game):
    """Render game over page."""
    current_player = ct_game.game_state.get_current_player()
    if not current_player:
        log_info("No current player found for rendering player page.")
        return redirect(url_for("index"))

    is_demon_alive = any(
        player.alive == PlayerStatus.ALIVE
        and player.character is not None
        and player.character.role_type == RoleType.DEMON
        for player in ct_game.game_state.players
    )

    return render_template(
        "player_page_game_over.html",
        game_winner_text="Demon and Minions win the game!"
        if is_demon_alive
        else "Townfolks and outsiders win the game!",
        is_alive=current_player.alive == PlayerStatus.ALIVE,
        is_admin=current_player.is_admin,
    )
