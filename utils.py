import random
import copy

class Database:
    def __init__(self):
        # _data: mapowanie ID (client_id) -> rekord
        # _sid_index: mapowanie sid -> client_id
        self._data = {}
        self._sid_index = {}

    def add(self, record_id: str, record: dict):
        """Dodaje nowy rekord z podanym client_id, jeśli nie istnieje."""
        if record_id in self._data:
            raise ValueError(f"ID '{record_id}' już istnieje w bazie!")
        self._data[record_id] = record

        # Jeśli w rekordzie jest SID, zapamiętaj jego mapowanie
        sid = record.get("sid")
        if sid:
            self._sid_index[sid] = record_id

    def __getitem__(self, key: str) -> dict:
        """Umożliwia dostęp zarówno po client_id, jak i po sid."""
        # Sprawdź czy to client_id
        if key in self._data:
            return self._data[key]

        # Sprawdź czy to sid
        if key in self._sid_index:
            client_id = self._sid_index[key]
            return self._data[client_id]

        raise KeyError(f"Nie znaleziono rekordu o ID lub SID '{key}'")

    def __setitem__(self, record_id: str, record: dict):
        """Dodaje nowy rekord, jak add()"""
        self.add(record_id, record)

    def __contains__(self, key: str) -> bool:
        """Zwraca True, jeśli ID lub SID istnieje w bazie."""
        return key in self._data or key in self._sid_index

    def remove(self, key: str):
        """Usuwa rekord po ID lub SID."""
        if key in self._sid_index:
            record_id = self._sid_index.pop(key)
            self._data.pop(record_id, None)
        elif key in self._data:
            record = self._data.pop(key)
            sid = record.get("sid")
            if sid:
                self._sid_index.pop(sid, None)
        else:
            raise KeyError(f"ID lub SID '{key}' nie istnieje w bazie.")

    def get_all(self):
        """Zwraca pełną kopię danych."""
        return dict(self._data)
    
    def __len__(self):
        return len(self._data)
    
    def get_all_client_ids(self):
        """Zwraca listę wszystkich client_id w bazie."""
        return list(self._data.keys())


import random
import copy

def assign_players_to_characters(client_ids, trouble_brewing_setup, db_characters):
    """
    Tworzy nową bazę postaci dla gry bez modyfikowania oryginalnej bazy db_characters,
    poza oznaczeniem które postacie zostały wybrane (pole 'wybrany': True/False).

    Zasady:
    - Tworzy nową bazę postaci (new_db_characters) na podstawie setupu.
    - Pijak dostaje dodatkową postać (lista jednoelementowa w 'druga_postac').
    - Imp dostaje 3 dodatkowych Mieszczan ('druga_postac' = lista 3 nazw).
    - Postacie wybrane dla Impa lub Pijaka nie mogą pojawić się nigdzie indziej.
    """
    liczba_graczy = len(client_ids)

    # Znajdź odpowiedni setup dla liczby graczy
    setup = next((s for s in trouble_brewing_setup if s["gracze"] == liczba_graczy), None)
    if setup is None:
        raise ValueError(f"Brak konfiguracji dla {liczba_graczy} graczy")

    # Zawsze resetuj flagę wyboru przed nowym losowaniem.
    # Bez tego kolejne gry dziedziczą stan poprzedniego losowania.
    for category in db_characters.values():
        for char in category:
            char["wybrany"] = False

    # Utwórz nową bazę danych dla bieżącej gry
    new_db_characters = {"Mieszkańcy": [], "Outsiderzy": [], "Minionki": [], "Demon": []}

    # Losuj postacie według setupu
    for category in ["Mieszkańcy", "Outsiderzy", "Minionki", "Demon"]:
        available = [c for c in db_characters[category] if not c.get("wybrany", False)]
        count = setup[category]
        if count > len(available):
            raise ValueError(f"Za mało dostępnych postaci w kategorii {category}")

        selected = random.sample(available, count)

        # Oznacz w oryginalnej bazie, że zostały wybrane
        for c in selected:
            c["wybrany"] = True

        # Dodaj kopie do nowej bazy
        for c in selected:
            new_char = copy.deepcopy(c)
            new_char["client_id"] = None
            new_char["numer_siedzenia"] = None
            new_db_characters[category].append(new_char)

    # Lista wszystkich wylosowanych postaci
    all_characters = (
        new_db_characters["Mieszkańcy"]
        + new_db_characters["Outsiderzy"]
        + new_db_characters["Minionki"]
        + new_db_characters["Demon"]
    )

    # Przetasuj graczy i postacie
    random.shuffle(client_ids)
    random.shuffle(all_characters)

    drunk_extra_pending = None
    imp_extra_pending = None

    # Przydziel postacie graczom
    for client_id, char in zip(client_ids, all_characters):
        char["client_id"] = client_id
        if char["name"] == "Pijak":
            drunk_extra_pending = client_id
        elif char["name"] == "Imp":
            imp_extra_pending = client_id

    # ======= Pijak =======
    if drunk_extra_pending:
        remaining_townsfolk = [
            c for c in db_characters["Mieszkańcy"] if not c.get("wybrany", False)
        ]
        if remaining_townsfolk:
            extra = random.choice(remaining_townsfolk)
            extra["wybrany"] = True  # oznacz w oryginalnej bazie, by już nie był dostępny
            extra_copy = copy.deepcopy(extra)
            extra_copy["client_id"] = drunk_extra_pending
            extra_copy["numer_siedzenia"] = None
            new_db_characters["Mieszkańcy"].append(extra_copy)

            # dopisz w rekordzie Pijaka jego dodatkową postać (lista)
            for category in new_db_characters.values():
                for c in category:
                    if c["name"] == "Pijak" and c["client_id"] == drunk_extra_pending:
                        c["druga_postac"] = [extra_copy["name"]]

    # ======= Imp =======
    if imp_extra_pending:
        remaining_townsfolk = [
            c for c in db_characters["Mieszkańcy"] if not c.get("wybrany", False)
        ]
        if len(remaining_townsfolk) >= 3:
            extra_three = random.sample(remaining_townsfolk, 3)
            # oznacz te postacie jako zużyte
            for e in extra_three:
                e["wybrany"] = True
            # dodaj ich kopie do nowej bazy, przypisane do tego samego gracza (Impa)
            for e in extra_three:
                extra_copy = copy.deepcopy(e)
                extra_copy["client_id"] = imp_extra_pending
                extra_copy["numer_siedzenia"] = None
                new_db_characters["Mieszkańcy"].append(extra_copy)

            # dopisz w rekordzie Impa jego dodatkowe postacie
            for category in new_db_characters.values():
                for c in category:
                    if c["name"] == "Imp" and c["client_id"] == imp_extra_pending:
                        c["druga_postac"] = [e["name"] for e in extra_three]

    # Debug – wypisz przydział
    print("📜 Wynik losowania postaci (nowa baza):")
    for category, chars in new_db_characters.items():
        print(f"\n{'=' * 50}")
        print(f"{category.upper()}")
        print(f"{'=' * 50}")
        for c in chars:
            extra_info = f" (druga_postac: {c.get('druga_postac')})" if "druga_postac" in c else ""
            print(f"{c['name']:20} | gracz: {c['client_id']} | numer_siedzenia: {c['numer_siedzenia']}{extra_info}")

    return new_db_characters


import random

def fun_praczka(characters, players, drunk=False):
    """
    Funkcja dla postaci 'Praczka'.
    Jeśli drunk=False:
        - losuje 1 postać z Mieszkańców oraz 1 postać z całej bazy
        - przypisuje listę tych postaci do pola 'druga_postac' wylosowanego Mieszkańca
        - ustawia tekst statusu z losową kolejnością imion graczy powiązanych z tymi postaciami.
    Jeśli drunk=True:
        - losuje 2 losowe imiona z bazy graczy
        - losuje 1 postać z Mieszkańców
        - zwraca komunikat z tymi danymi
    """

    print(characters)
    all_chars = [c for chars in characters.values() for c in chars]
    mieszkancy = characters.get("Mieszkańcy", [])

    if not mieszkancy or len(all_chars) < 2:
        return "Brak wystarczającej liczby postaci do losowania."

    if drunk:
        # --- Tryb "Pijaka" ---
        mieszkaniec = random.choice(mieszkancy)
        losowi_gracze = random.sample(list(players.values()), 2)
        name1, name2 = losowi_gracze[0]["name"], losowi_gracze[1]["name"]

        tekst = (
            f"Tylko jeden z graczy: {name1} oraz {name2} "
            f"ma postać: {mieszkaniec['name']}"
        )

    else:
        # --- Tryb normalny ---
        mieszkaniec = random.choice(mieszkancy)
        druga_postac = random.choice([c for c in all_chars if c != mieszkaniec])

        # Zapisz drugą postać (lista, jak wymagano)
        mieszkaniec["druga_postac"] = [mieszkaniec["name"], druga_postac["name"]]

        # Pobierz imiona graczy
        print(mieszkaniec.get("client_id"))
        print(druga_postac.get("client_id"))
        player1 = players[mieszkaniec.get("client_id")]
        player2 = players[druga_postac.get("client_id")]

        name1 = player1["name"] if player1 else "Nieznany"
        name2 = player2["name"] if player2 else "Nieznany"

        # Losowa kolejność imion
        names = [name1, name2]
        random.shuffle(names)

        tekst = (
            f"Tylko jeden z graczy: {names[0]} oraz {names[1]} "
            f"ma postać: {mieszkaniec['name']}"
        )

    # Zapisz status w bazie
    mieszkaniec["player_status"] = tekst
    return tekst


def fun_bibliotekarka(characters, players):
    return "Na razie nic."

def fun_detektyw(characters, players):
    return "Na razie nic."

def fun_kucharz(characters, players):
    return "Na razie nic."

def fun_empata(characters, players):
    return "Na razie nic."

def fun_wrozka(characters, players):
    return "Na razie nic."

def fun_kantor(characters, players):
    return "Na razie nic."

def fun_mnich(characters, players):
    return "Na razie nic."

def fun_krukopiek(characters, players):
    return "Na razie nic."

def fun_dziewica(characters, players):
    return "Na razie nic."

def fun_zabojca(characters, players):
    return "Na razie nic."

def fun_zolnierz(characters, players):
    return "Na razie nic."

def fun_burmistrz(characters, players):
    return "Na razie nic."

def fun_lokaj(characters, players):
    return "Na razie nic."

def fun_pijak(characters, players):
    return "Na razie nic."

def fun_samotnik(characters, players):
    return "Na razie nic."

def fun_swiety(characters, players):
    return "Na razie nic."

def fun_truciciel(characters, players):
    return "Na razie nic."

def fun_szpieg(characters, players):
    return "Na razie nic."

def fun_scarlet(characters, players):
    return "Na razie nic."

def fun_baron(characters, players):
    return "Na razie nic."

def fun_imp(characters, players):
    return "Na razie nic."
