from characters.character import RoleType
from logger import log_info
from player import PlayerStatus

KNOWLEDGE_VALUE = {"zero": 0, "weak": 1, "medium": 2, "strong": 4, "confirmed": 6}


class WinnerHeuristic:
    def __init__(self, game_state, character_power):
        self.game_state = game_state
        self.character_power = character_power
        log_info("WinnerHeuristic initialized with game state.")

    def evaluate_player_count(self) -> float:
        """
        Evaluate player count and return a score indicating the advantage for the good or evil team.

        This simply answers: "Is there more good or evil players alive?"
        and applies a multiplier based on how many players are left in the game.
        The score is positive if good has more alive players, negative if evil has more alive players.

        """
        good_alive = 0
        evil_alive = 0

        for player in self.game_state.players:
            if not player.alive == PlayerStatus.ALIVE:
                continue

            if player.character.role_type in [RoleType.TOWNSFOLK, RoleType.OUTSIDER]:
                good_alive += 1
            elif player.character.role_type in [RoleType.DEMON, RoleType.MINION]:
                evil_alive += 1

        total_alive = good_alive + evil_alive
        delta = good_alive - evil_alive
        log_info(
            f"[WinnerHeuristic] Evaluating player count: {good_alive} good alive, {evil_alive} evil alive, delta: {delta}"
        )

        if evil_alive == 1:
            return 20.0  # został tylko demon

        if delta <= 0:
            return -20.0  # zło osiągnęło przewagę lub jest równe do dobra

        if total_alive >= 8:
            phase_weight = 1.0
        elif total_alive >= 6:
            phase_weight = 1.5
        else:
            phase_weight = 2.5

        score = delta * phase_weight

        mistake_margin = delta - 1

        if mistake_margin == 0:
            score -= 8
        elif mistake_margin == 1:
            score -= 4
        elif mistake_margin >= 4:
            score += 4

        log_info(f"[WinnerHeuristic] Player count score: {score}")
        return score

    def evaluate_alive_characters(self) -> float:
        """
        Evaluate the characters of alive players and return a score indicating the advantage for the good or evil team.

        This should answer: "How strong are the characters that are still alive on each team?"
        """
        score = 0.0

        for player in self.game_state.players:
            character = player.character.name

            power = self.character_power.get(character, 0)
            log_info(
                f"[WinnerHeuristic] Evaluating character {character} with base power {power}."
            )

            # Martwe postaci nadal mają częściową wartość
            if not player.alive == PlayerStatus.ALIVE:
                power *= 0.3

            # Dobrzy dodają score
            if player.character.role_type in [RoleType.TOWNSFOLK, RoleType.OUTSIDER]:
                score += power

            # Źli odejmują score
            elif player.character.role_type in [RoleType.DEMON, RoleType.MINION]:
                score += power  # już mają wartości ujemne

        log_info(f"[WinnerHeuristic] Alive characters score: {score}")
        return score

    def evaluate_good_knowledge(self) -> float:
        """Evaluate the knowledge of good players and return a score indicating the advantage for the good team."""
        score = 0.0

        for player in self.game_state.players:
            if player.character.role_type in [RoleType.DEMON, RoleType.MINION]:
                continue

            if hasattr(player.character, "evaluate_knowledge_score"):
                knowledge = player.character.evaluate_knowledge_score(player)
                power = self.character_power.get(player.character.name, 1)
                log_info(
                    f"[WinnerHeuristic] Evaluating good knowledge for {player.character.name}: {knowledge} (power: {power})"
                )

                # Martwi nadal mogą dzielić się wiedzą,
                # ale trochę mniej wpływają
                if not player.alive == PlayerStatus.ALIVE:
                    knowledge *= 0.7

                score += knowledge * power

        log_info(f"[WinnerHeuristic] Good knowledge score: {score}")
        return score

    def evaluate_misinformation(self) -> float:
        """Evaluate the misinformation affecting good players and return a score indicating the disadvantage for the good team."""
        score = 0.0

        for player in self.game_state.players:
            if player.character.role_type in [RoleType.DEMON, RoleType.MINION]:
                continue

            penalty = 0.0
            power = self.character_power.get(player.character.name, 0)
            log_info(
                f"[WinnerHeuristic] Evaluating misinformation for {player.character.name} with base power {power}."
            )

            if player.poisoned:
                penalty += 2.0 * power

            if player.drunk:
                penalty += 3.0 * power

            if (
                hasattr(player.character, "has_bad_info")
                and player.character.has_bad_info
            ):
                penalty += 3.0 * power

            if not player.alive == PlayerStatus.ALIVE:
                penalty *= 0.7

            score -= penalty

        log_info(f"[WinnerHeuristic] Misinformation score: {score}")
        return score

    def evaluate_voting_history(self) -> float:
        score = 0.0
        voting_snapshot = self.game_state.get_last_day_voting_snapshot()
        log_info(
            "[WinnerHeuristic] Evaluating voting history for last day nominated players: "
            f"{[p.get('character_name') for p in voting_snapshot]}"
        )

        for nominee in voting_snapshot:
            nominee_votes = nominee.get("votes", 0)
            nominee_role_type = nominee.get("role_type")

            # 1. Sama presja głosów
            if nominee_role_type in [RoleType.DEMON, RoleType.MINION]:
                score += nominee_votes * 2.0

                if nominee_role_type in [RoleType.DEMON]:
                    score += nominee_votes * 3.0

            else:
                score -= nominee_votes * 1.5

        # 2. Faktyczna egzekucja (niezależnie od tego, czy są aktywne nominacje)
        last_executed_player = self.game_state.last_executed_player
        if last_executed_player:
            if last_executed_player.character.role_type in [
                RoleType.DEMON,
                RoleType.MINION,
            ]:
                score += 6.0
                if last_executed_player.character.role_type in [RoleType.DEMON]:
                    score += 20.0
                else:
                    score += 3.0

            else:
                score -= 5.0

                if last_executed_player.character.name in [
                    "Jasnowidz",
                    "Grabarz",
                    "Empata",
                    "Dziewica",
                    "Burmistrz",
                ]:
                    score -= 3.0

        log_info(f"[WinnerHeuristic] Voting history score: {score}")
        return score

    def evaluate_endgame(self) -> float:
        """Evaluate the endgame state and return a score indicating the advantage for the good or evil team."""
        score = 0.0

        good_alive = 0
        evil_alive = 0

        for player in self.game_state.players:
            if not player.alive == PlayerStatus.ALIVE:
                continue

            if player.character.role_type in [RoleType.TOWNSFOLK, RoleType.OUTSIDER]:
                good_alive += 1
            elif player.character.role_type in [RoleType.DEMON, RoleType.MINION]:
                evil_alive += 1

        alive = good_alive + evil_alive
        mistake_margin = good_alive - evil_alive - 1

        # 1. Margines błędu dobra
        if mistake_margin <= 0:
            score -= 10.0

        elif mistake_margin == 1:
            score -= 5.0

        elif mistake_margin >= 3:
            score += 3.0

        # 2. Krytyczne stany końcówki
        if alive == 3:
            score -= 8.0

        elif alive == 4:
            score -= 4.0

        elif alive == 5:
            score -= 2.0

        # 3. Presja na demona
        nominated_players = self.game_state.get_nominated_players()
        demon = None
        for player in nominated_players:
            if player.character.role_type in [RoleType.DEMON]:
                demon = player
                break

        if demon:
            score += 4.0
            if demon.number_of_votes >= 2:
                score += 3.0

        # 4. Endgame role
        for player in self.game_state.players:
            if player.alive != PlayerStatus.ALIVE:
                continue
            elif player.character.name == "Burmistrz":
                score += 3.0
            elif player.character.name == "Swiety":
                score -= 4.0
            elif player.character.name == "Skarlet":
                score -= 4.0

        log_info(f"[WinnerHeuristic] Endgame score: {score}")
        return score

    def evaluate_game_advantage(self):
        score = 0

        score_player_count = self.evaluate_player_count()
        score_alive_characters = self.evaluate_alive_characters()
        score_good_knowledge = self.evaluate_good_knowledge()
        score_misinformation = self.evaluate_misinformation()
        score_voting_history = self.evaluate_voting_history()
        score_endgame = self.evaluate_endgame()

        score = (
            score_player_count
            + score_alive_characters
            + score_good_knowledge
            - score_misinformation
            + score_voting_history
            + score_endgame
        )

        log_info(f"[WinnerHeuristic] Total advantage score: {score}")
        log_info(
            "\n[WinnerHeuristic] Score elements: "
            + ", \n".join(
                [
                    f"Player count: {score_player_count}",
                    f"Alive characters: {score_alive_characters}",
                    f"Good knowledge: {score_good_knowledge}",
                    f"Misinformation: {score_misinformation}",
                    f"Voting history: {score_voting_history}",
                    f"Endgame: {score_endgame}",
                ]
            )
        )

        return score
