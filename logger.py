"""Module for handling logging in the Mafia game."""

import logging
import os
from logging.handlers import RotatingFileHandler


class FileLogger:
    def __init__(self, name="app_logger"):
        """Handle init."""
        self.logger = logging.getLogger(name)
        self.game_state = None  # To be set later by the state machine

        # żeby nie dodawać handlerów wiele razy
        if self.logger.handlers:
            return

        self.logger.setLevel(logging.INFO)

        # folder na logi
        os.makedirs("logs", exist_ok=True)

        # handler do pliku (rotacja!)
        file_handler = RotatingFileHandler(
            "logs/game_server.log", maxBytes=1_000_000, backupCount=3  # 1 MB
        )

        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)

    def log_info(self, message: str, *args):
        """Handle log info."""
        self.logger.info(message, *args)

    def log_error(self, message: str, *args):
        """Handle log error."""
        self.logger.error(message, *args)


# =========================
# INICJALIZACJA
# =========================

LOGGER = FileLogger()


def log_info(message: str, *args):
    """Handle log info."""
    LOGGER.log_info(message, *args)


def log_error(message: str, *args):
    """Handle log error."""
    LOGGER.log_error(message, *args)
