import random

from logger import log_info

KNOWLEDGE_VALUE = {"zero": 0, "weak": 1, "medium": 2, "strong": 4, "confirmed": 6}


class RecluseHeuristic:
    def __init__(self, game_state, winner_heuristic):
        self.game_state = game_state
        log_info("RecluseHeuristic initialized with game state.")
        self.winner_heuristic = winner_heuristic
        self.score_cache = 0.0
        self.recluse_context_weight = {
            "Jasnowidz": 1.0,
            "Detektyw": 1.2,
            "Grabarz": 0.8,
            "Empata": 0.7,
            "Kucharz": 0.6,
            "Zabojca": 0.4,
        }
        # Dodaj pamięć dla contextów
        self.recluse_memory = {}
        # Licznik zapytań o character registration w danym dniu/nocy
        self.recluse_query_counter = 0
        self.recluse_last_phase = None

    def evaluate_game_advantage(self):
        score = self.winner_heuristic.evaluate_game_advantage()
        self.score_cache = score
        self.set_new_phase()
        log_info(
            f"[RecluseHeuristic] Base advantage score from WinnerHeuristic: {score}"
        )

    def set_new_phase(self):
        """Reset licznik zapytań jeśli zmieniła się faza (dzień/noc)."""
        self.recluse_query_counter = 0

    def get_recluse_fake_chance(self):
        if self.score_cache >= 35:
            return 1.0  # dobro mocno prowadzi
        if self.score_cache >= 25:
            return 0.90
        if self.score_cache >= 12:
            return 0.75
        if self.score_cache >= 5:
            return 0.60
        if self.score_cache > -5:
            return 0.45  # gra wyrównana
        if self.score_cache > -12:
            return 0.25
        if self.score_cache > -25:
            return 0.10
        return 0.0  # zło bardzo prowadzi

    def should_recluse_fake(self, context: str) -> bool:
        # Zmniejsz szansę na kłamstwo o 25% za każde kolejne zapytanie w tej samej fazie
        base_chance = self.get_recluse_fake_chance()
        context_weight = self.recluse_context_weight.get(context, 1.0)
        # Każde kolejne zapytanie zmniejsza szansę o 25% (czyli *0.75)
        chance = base_chance * context_weight * (0.75**self.recluse_query_counter)
        chance = max(0.0, min(chance, 0.95))
        self.recluse_query_counter += 1
        log_info(
            f"[RecluseHeuristic] Context: {context}, Base fake chance: {base_chance:.2f}, Context weight: {context_weight}, Query count: {self.recluse_query_counter}, Final fake chance: {chance:.2f}"
        )
        decision = random.random() < chance
        log_info(
            f"[RecluseHeuristic] Recluse decides to {'fake' if decision else 'tell the truth'} for context: {context}"
        )
        return decision

    def get_recluse_registered_character(self, context: str):
        # Jeśli już pamiętamy odpowiedź dla tego contextu, zwróć ją
        if context in self.recluse_memory:
            return self.recluse_memory[context]

        recluse_fake = self.should_recluse_fake(context)

        if not recluse_fake:
            self.recluse_memory[context] = "Pustelnik"
            return "Pustelnik"

        evil_options = ["Imp", "Truciciel", "Szpieg", "Baron", "Skarlet"]
        chosen = random.choice(evil_options)
        self.recluse_memory[context] = chosen
        log_info(
            f"[RecluseHeuristic] Pustelnik decides to fake as: {chosen} in context: {context}"
        )
        return chosen

    def grabarz_asks_for_character(self, executed_player):
        if executed_player.character.name == "Pustelnik":
            return self.get_recluse_registered_character("Grabarz")
        return executed_player.character.name

    def krukarz_asks_for_character(self, target_player):
        if target_player.character.name == "Pustelnik":
            return self.get_recluse_registered_character("Krukarz")
        return target_player.character.name

    def empata_asks_for_neighbors(self, player):
        if player.character.name == "Pustelnik":
            return self.get_recluse_registered_character("Empata")
        return (
            None  # Empata i tak nie dostaje informacji o sąsiadach, więc zwracamy None
        )

    def kucharz_asks_for_evil_pairs(self, player):
        if player.character.name == "Pustelnik":
            return self.get_recluse_registered_character("Kucharz")
        return None  # Kucharz i tak nie dostaje informacji o parach złych graczy, więc zwracamy None

    def zabojca_asks_for_demon(self, player):
        if player.character.name == "Pustelnik":
            return self.get_recluse_registered_character("Zabojca")
        return (
            None  # Zabojca i tak nie dostaje informacji o demonie, więc zwracamy None
        )

    def detektyw_asks_for_demon(self, player):
        if player.character.name == "Pustelnik":
            return self.get_recluse_registered_character("Detektyw")
        return (
            None  # Detektyw i tak nie dostaje informacji o minionie, więc zwracamy None
        )
