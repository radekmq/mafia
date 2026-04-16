"""Module for handling state machine utilities in the Mafia game."""

import random

from characters.characters_data import CHARACTERS_BY_TYPE
from game_setup import TROUBLE_BREWING_SETUP
from game_state import GameState
from logger import log_error, log_info


# pylint: disable=too-many-locals
def log_players_status_table(game_state: GameState):
    """Handle log players status table."""
    players = list(game_state.players)
    if not players:
        log_info("Brak graczy do wyświetlenia w tabeli statusu.")
        return

    headers = [
        "Nazwa gracza",
        "Seat",
        "Postać",
        "Dodatkowe postaci",
        "Pijany",
        "Poisoned",
        "Alive",
        "Protected",
    ]

    rows = []
    for player in players:
        character_name = player.character.name if player.character else "-"
        additional = (
            ", ".join(char.name for char in (player.additional_characters or [])) or "-"
        )
        drunk = "TAK" if player.drunk else "NIE"
        poisoned = "TAK" if player.poisoned else "NIE"
        protected = "TAK" if player.protected else "NIE"
        alive = (
            player.alive.value.upper()
            if hasattr(player.alive, "value")
            else str(player.alive)
        )

        rows.append(
            [
                player.name,
                player.seat_no,
                character_name,
                additional,
                drunk,
                poisoned,
                alive,
                protected,
            ]
        )

    widths = [len(header) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(str(value)))

    def format_row(values):
        """Handle format row."""
        return (
            "| "
            + " | ".join(
                str(value).ljust(widths[index]) for index, value in enumerate(values)
            )
            + " |"
        )

    separator = "+-" + "-+-".join("-" * width for width in widths) + "-+"

    table_lines = [separator, format_row(headers), separator]
    for row in rows:
        table_lines.append(format_row(row))
    table_lines.append(separator)

    log_info("Status graczy:\n" + "\n".join(table_lines))


# pylint: disable=too-many-locals,too-many-statements
def assign_random_characters(game_state: GameState):
    """Handle assign random characters."""
    player_count = len(game_state.players)
    setup = next(
        (row for row in TROUBLE_BREWING_SETUP if row["gracze"] == player_count), None
    )
    if not setup:
        log_info(f"Brak setupu dla liczby graczy: {player_count}")
        return

    no_of_demons = setup["Demon"]
    no_of_minions = setup["Minionki"]
    no_of_outsiders = setup["Outsiderzy"]
    no_of_townsfolk = setup["Mieszkańcy"]

    pool_demons = list(CHARACTERS_BY_TYPE["demon"])
    pool_minions = list(CHARACTERS_BY_TYPE["minion"])
    pool_outsiders = list(CHARACTERS_BY_TYPE["outsider"])
    pool_townsfolk = list(CHARACTERS_BY_TYPE["townsfolk"])

    all_players = list(game_state.players)
    random.shuffle(all_players)

    assigned = []
    used_routes = set()

    def draw_from_pool(pool, count, pool_name):
        """Handle draw from pool."""
        available = [char for char in pool if char.route not in used_routes]
        if len(available) < count:
            log_error(
                "Za mało postaci w puli "
                f"'{pool_name}'. Potrzeba: {count}, dostępne: {len(available)}"
            )
            raise ValueError(
                "Za mało postaci w puli "
                f"'{pool_name}'. Potrzeba: {count}, dostępne: {len(available)}"
            )
        drawn = random.sample(available, count)
        for char in drawn:
            used_routes.add(char.route)
        return drawn

    # 1. Demon(y)
    demons = draw_from_pool(pool_demons, no_of_demons, "demon")
    assigned.extend(demons)

    # 2. Trzy dodatkowe postacie dla Impa z Townsfolk/Outsider bez powtórek.
    if no_of_demons > 0:
        demon_extra_pool = [
            char
            for char in (pool_townsfolk + pool_outsiders)
            if char.route not in used_routes
        ]
        if len(demon_extra_pool) < 3:
            log_error(
                "Za mało postaci na dodatkowe role dla demona. "
                f"Potrzeba: 3, dostępne: {len(demon_extra_pool)}"
            )
            raise ValueError(
                "Za mało postaci na dodatkowe role dla demona. "
                f"Potrzeba: 3, dostępne: {len(demon_extra_pool)}"
            )
        demon_additional = random.sample(demon_extra_pool, 3)
        for char in demon_additional:
            used_routes.add(char.route)

    # 3. Minion(y)
    minions = draw_from_pool(pool_minions, no_of_minions, "minion")
    assigned.extend(minions)

    # 4. Outsiderzy
    outsiders = draw_from_pool(pool_outsiders, no_of_outsiders, "outsider")
    assigned.extend(outsiders)

    # 4a. Dla Pijaka losujemy dodatkową postać z Townsfolk bez powtórek.
    drunk_fake_role = None
    if any(char.route == "pijak" for char in outsiders):
        drunk_fake_role = draw_from_pool(pool_townsfolk, 1, "townsfolk (dla Pijaka)")[0]

    # 5. Mieszkańcy
    townsfolk = draw_from_pool(pool_townsfolk, no_of_townsfolk, "townsfolk")
    assigned.extend(townsfolk)

    if len(assigned) != player_count:
        log_error(
            "Liczba przypisanych postaci "
            f"({len(assigned)}) nie zgadza się z liczbą graczy ({player_count})"
        )
        raise ValueError(
            "Liczba przypisanych postaci "
            f"({len(assigned)}) nie zgadza się z liczbą graczy ({player_count})"
        )

    random.shuffle(assigned)
    demon_extras_assigned = False
    drunk_assigned = False

    for player, character in zip(all_players, assigned):
        player.character = character

        if character.role_type.value == "demon" and not demon_extras_assigned:
            player.additional_characters = list(demon_additional)
            demon_extras_assigned = True

        if character.route == "pijak":
            player.drunk = True
            if drunk_fake_role and not drunk_assigned:
                player.additional_characters.append(drunk_fake_role)
                drunk_assigned = True

    log_info(
        f"Rozdano role: demon={no_of_demons}, minionki={no_of_minions}, "
        f"outsiderzy={no_of_outsiders}, mieszkańcy={no_of_townsfolk}"
    )
