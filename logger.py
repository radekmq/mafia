"""Module for handling logging in the Mafia game."""

import logging
import os
from logging.handlers import RotatingFileHandler

from flask import has_request_context, session

from database import GAME_STATE


# Ignore logging for /api/state endpoint to reduce noise in logs
# pylint: disable=too-few-public-methods
class IgnoreApiState(logging.Filter):
    """Logging filter to ignore /api/state endpoint logs."""

    def filter(self, record):
        """Handle filter."""
        return "/api/state" not in record.getMessage()


def get_logger(name="app_logger"):
    """Handle get logger."""
    logger = logging.getLogger(name)

    # żeby nie dodawać handlerów wiele razy
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # folder na logi
    os.makedirs("logs", exist_ok=True)

    # handler do pliku (rotacja!)
    file_handler = RotatingFileHandler(
        "logs/game_server.log", maxBytes=1_000_000, backupCount=3  # 1 MB
    )

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger


def log_info(message: str):
    """Handle log info."""
    if has_request_context():
        client_id = session.get("client_id")
    else:
        client_id = None

    player_name = GAME_STATE.get_player_name(client_id) if client_id else None
    if player_name:
        LOGGER.info("[%s] %s", player_name, message)
    else:
        LOGGER.info("[Unknown player] %s", message)


def log_error(message: str):
    """Handle log error."""
    if has_request_context():
        client_id = session.get("client_id")
    else:
        client_id = None

    player_name = GAME_STATE.get_player_name(client_id) if client_id else None
    if player_name:
        LOGGER.error("[%s] %s", player_name, message)
    else:
        LOGGER.error("[Unknown player] %s", message)


# =========================
# INICJALIZACJA
# =========================

LOGGER = get_logger()
