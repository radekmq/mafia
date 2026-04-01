import random
import copy

test_enabled = False

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

def assign_players_to_characters(client_ids, trouble_brewing_setup, db_characters, players_db=None):
    """
    Tworzy nową bazę postaci dla gry bez modyfikowania oryginalnej bazy db_characters,
    poza oznaczeniem które postacie zostały wybrane (pole 'wybrany': True/False).

    Zasady:
    - Tworzy nową bazę postaci (new_db_characters) na podstawie setupu.
    - Pijak dostaje dodatkową postać (lista jednoelementowa w 'druga_postac').
    - Imp dostaje 3 dodatkowych Mieszczan ('druga_postac' = lista 3 nazw).
    - Postacie wybrane dla Impa lub Pijaka nie mogą pojawić się nigdzie indziej.
    """
    print("\n[assign_players_to_characters] Start losowania")
    print(f"[assign_players_to_characters] client_ids before shuffle: {client_ids}")
    liczba_graczy = len(client_ids)
    print(f"[assign_players_to_characters] liczba_graczy={liczba_graczy}")

    forced_praczka_client_id = None
    if test_enabled and players_db:
        for player_client_id, player in players_db.items():
            if player.get("name") == "RadekP":
                forced_praczka_client_id = player_client_id
                break
        print(
            f"[assign_players_to_characters] TEST MODE: forced_praczka_client_id="
            f"{forced_praczka_client_id}"
        )

    # Znajdź odpowiedni setup dla liczby graczy
    setup = next((s for s in trouble_brewing_setup if s["gracze"] == liczba_graczy), None)
    if setup is None:
        print(f"[assign_players_to_characters] Brak setupu dla liczby graczy={liczba_graczy}")
        raise ValueError(f"Brak konfiguracji dla {liczba_graczy} graczy")
    print(f"[assign_players_to_characters] Wybrany setup: {setup}")

    # Zawsze resetuj flagę wyboru przed nowym losowaniem.
    # Bez tego kolejne gry dziedziczą stan poprzedniego losowania.
    for category in db_characters.values():
        for char in category:
            char["wybrany"] = False
    print("[assign_players_to_characters] Zresetowano flagi 'wybrany' dla wszystkich postaci")

    # Utwórz nową bazę danych dla bieżącej gry
    new_db_characters = {"Mieszkańcy": [], "Outsiderzy": [], "Minionki": [], "Demon": []}

    # Losuj postacie według setupu
    for category in ["Mieszkańcy", "Outsiderzy", "Minionki", "Demon"]:
        available = [c for c in db_characters[category] if not c.get("wybrany", False)]
        count = setup[category]
        print(
            f"[assign_players_to_characters] Kategoria={category}, "
            f"potrzeba={count}, dostepne={len(available)}, "
            f"nazwy={[c['name'] for c in available]}"
        )
        if count > len(available):
            print(f"[assign_players_to_characters] Za mało postaci w kategorii={category}")
            raise ValueError(f"Za mało dostępnych postaci w kategorii {category}")

        selected = random.sample(available, count)

        if category == "Mieszkańcy" and forced_praczka_client_id and count > 0:
            praczka = next((c for c in available if c.get("name") == "Praczka"), None)
            if praczka and praczka not in selected:
                replace_idx = random.randrange(len(selected))
                replaced = selected[replace_idx]
                selected[replace_idx] = praczka
                print(
                    "[assign_players_to_characters] TEST MODE: wymuszono Praczkę "
                    f"(zamiana {replaced['name']} -> Praczka)"
                )

        print(
            f"[assign_players_to_characters] Wylosowane w kategorii={category}: "
            f"{[c['name'] for c in selected]}"
        )

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
    print(
        "[assign_players_to_characters] Wszystkie wylosowane postacie przed shuffle: "
        f"{[c['name'] for c in all_characters]}"
    )

    # Przetasuj graczy i postacie
    random.shuffle(client_ids)
    random.shuffle(all_characters)

    if forced_praczka_client_id and forced_praczka_client_id in client_ids:
        forced_idx = client_ids.index(forced_praczka_client_id)
        praczka_idx = next(
            (idx for idx, char in enumerate(all_characters) if char.get("name") == "Praczka"),
            None,
        )
        if praczka_idx is not None:
            all_characters[forced_idx], all_characters[praczka_idx] = (
                all_characters[praczka_idx],
                all_characters[forced_idx],
            )
            print(
                "[assign_players_to_characters] TEST MODE: przypisano Praczkę "
                f"do client_id={forced_praczka_client_id}"
            )
        else:
            print("[assign_players_to_characters] TEST MODE: Praczka nie została znaleziona")

    print(f"[assign_players_to_characters] client_ids after shuffle: {client_ids}")
    print(
        "[assign_players_to_characters] all_characters after shuffle: "
        f"{[c['name'] for c in all_characters]}"
    )

    drunk_extra_pending = None
    imp_extra_pending = None

    # Przydziel postacie graczom
    for client_id, char in zip(client_ids, all_characters):
        char["client_id"] = client_id
        if players_db and client_id in players_db:
            char["numer_siedzenia"] = players_db[client_id].get("seat")
        print(
            f"[assign_players_to_characters] Przydzielono postac={char['name']} "
            f"do client_id={client_id}"
        )
        if char["name"] == "Pijak":
            drunk_extra_pending = client_id
        elif char["name"] == "Imp":
            imp_extra_pending = client_id

    print(f"[assign_players_to_characters] drunk_extra_pending={drunk_extra_pending}")
    print(f"[assign_players_to_characters] imp_extra_pending={imp_extra_pending}")

    # ======= Pijak =======
    if drunk_extra_pending:
        remaining_townsfolk = [
            c for c in db_characters["Mieszkańcy"] if not c.get("wybrany", False)
        ]
        print(
            "[assign_players_to_characters] Dostepni Mieszkancy dla Pijaka: "
            f"{[c['name'] for c in remaining_townsfolk]}"
        )
        if remaining_townsfolk:
            extra = random.choice(remaining_townsfolk)
            extra["wybrany"] = True  # oznacz w oryginalnej bazie, by już nie był dostępny
            extra_copy = copy.deepcopy(extra)
            extra_copy["client_id"] = drunk_extra_pending
            extra_copy["numer_siedzenia"] = None
            new_db_characters["Mieszkańcy"].append(extra_copy)
            print(
                f"[assign_players_to_characters] Pijak client_id={drunk_extra_pending} "
                f"otrzymal dodatkowa postac={extra_copy['name']}"
            )

            # dopisz w rekordzie Pijaka jego dodatkową postać (lista) i mapowanie maski
            for category in new_db_characters.values():
                for c in category:
                    if c["name"] == "Pijak" and c["client_id"] == drunk_extra_pending:
                        c["druga_postac"] = [extra_copy["name"]]
                        c["drunk_role_name"] = extra_copy["name"]
                        print(
                            "[assign_players_to_characters] Ustawiono maskowanie Pijaka: "
                            f"client_id={drunk_extra_pending}, real_role=Pijak, visible_role={extra_copy['name']}"
                        )
        else:
            print("[assign_players_to_characters] Brak dodatkowej postaci dla Pijaka")

    # ======= Imp =======
    if imp_extra_pending:
        remaining_townsfolk = [
            c for c in db_characters["Mieszkańcy"] if not c.get("wybrany", False)
        ]
        print(
            "[assign_players_to_characters] Dostepni Mieszkancy dla Impa: "
            f"{[c['name'] for c in remaining_townsfolk]}"
        )
        if len(remaining_townsfolk) >= 3:
            extra_three = random.sample(remaining_townsfolk, 3)
            print(
                f"[assign_players_to_characters] Imp client_id={imp_extra_pending} "
                f"otrzymal dodatkowe postacie={[e['name'] for e in extra_three]}"
            )
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
        else:
            print("[assign_players_to_characters] Brak wystarczajacej liczby dodatkowych postaci dla Impa")

    # Debug – wypisz przydział
    print("📜 Wynik losowania postaci (nowa baza):")
    for category, chars in new_db_characters.items():
        print(f"\n{'=' * 50}")
        print(f"{category.upper()}")
        print(f"{'=' * 50}")
        for c in chars:
            player_name = "Nieznany"
            if players_db and c.get("client_id") in players_db:
                player_name = players_db[c["client_id"]].get("name", "Nieznany")
            extra_info = f" (druga_postac: {c.get('druga_postac')})" if "druga_postac" in c else ""
            print(
                f"{c['name']:20} | gracz: {c['client_id']} ({player_name}) | "
                f"numer_siedzenia: {c['numer_siedzenia']}{extra_info}"
            )

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
    # Bierz pod uwage tylko postacie realnie uczestniczace w grze (z numerem miejsca).
    assigned_chars = [
        c for c in all_chars if c.get("client_id") in players and c.get("numer_siedzenia") is not None
    ]
    assigned_mieszkancy = [
        c for c in mieszkancy if c.get("client_id") in players and c.get("numer_siedzenia") is not None
    ]
    assigned_mieszkancy_without_praczka = [
        c for c in assigned_mieszkancy if c.get("name") != "Praczka"
    ]

    if not assigned_mieszkancy or len(assigned_chars) < 2:
        return "Brak wystarczającej liczby postaci do losowania."

    if not assigned_mieszkancy_without_praczka:
        return "Brak odpowiedniej postaci mieszkańca do informacji Praczki."

    def safe_player_name(client_id):
        if not client_id or client_id not in players:
            return "Nieznany"
        try:
            return players[client_id].get("name", "Nieznany")
        except KeyError:
            return "Nieznany"

    if drunk:
        # --- Tryb "Pijaka" ---
        if len(players) < 2:
            return "Brak wystarczającej liczby graczy do losowania."

        mieszkaniec = random.choice(assigned_mieszkancy_without_praczka)
        losowi_gracze = random.sample(list(players.get_all().values()), 2)
        name1, name2 = losowi_gracze[0]["name"], losowi_gracze[1]["name"]

        tekst = (
            f"Tylko jeden z graczy: {name1} oraz {name2} "
            f"ma postać: {mieszkaniec['name']}"
        )

    else:
        # --- Tryb normalny ---
        mieszkaniec = random.choice(assigned_mieszkancy_without_praczka)
        mieszkaniec_client_id = mieszkaniec.get("client_id")
        kandydaci = [
            c
            for c in assigned_chars
            if c.get("client_id") and c.get("client_id") != mieszkaniec_client_id
        ]
        if not kandydaci:
            return "Brak wystarczającej liczby różnych graczy do losowania."

        druga_postac = random.choice(kandydaci)

        # Zapisz drugą postać (lista, jak wymagano)
        mieszkaniec["druga_postac"] = [mieszkaniec["name"], druga_postac["name"]]

        # Pobierz imiona graczy
        print(mieszkaniec.get("client_id"))
        print(druga_postac.get("client_id"))
        name1 = safe_player_name(mieszkaniec.get("client_id"))
        name2 = safe_player_name(druga_postac.get("client_id"))

        # Losowa kolejność imion
        names = [name1, name2]
        random.shuffle(names)

        tekst = (
            f"Tylko jeden z graczy: {names[0]} oraz {names[1]} "
            f"ma postać: {mieszkaniec['name']}"
        )

    return tekst


def fun_bibliotekarka(characters, players, drunk=False):
    """
    Funkcja dla postaci 'Bibliotekarka'.
    Jeśli drunk=False:
        - gdy Outsider jest w grze: wskazuje 2 graczy, z których jeden ma konkretną postać Outsidera
        - gdy brak Outsiderów: informuje, że żaden Outsider nie jest w grze
    Jeśli drunk=True:
        - generuje losową informację o 2 graczach i losowym Outsiderze
    """

    all_chars = [c for chars in characters.values() for c in chars]
    outsiderzy = characters.get("Outsiderzy", [])
    # Bierz pod uwage tylko postacie realnie uczestniczace w grze (z numerem miejsca).
    assigned_chars = [
        c for c in all_chars if c.get("client_id") in players and c.get("numer_siedzenia") is not None
    ]
    assigned_outsiderzy = [
        c for c in outsiderzy if c.get("client_id") in players and c.get("numer_siedzenia") is not None
    ]

    if len(players) < 2:
        return "Brak wystarczającej liczby graczy do losowania."

    def safe_player_name(client_id):
        if not client_id or client_id not in players:
            return "Nieznany"
        try:
            return players[client_id].get("name", "Nieznany")
        except KeyError:
            return "Nieznany"

    if drunk:
        wszyscy_gracze = list(players.get_all().values())
        losowi_gracze = random.sample(wszyscy_gracze, 2)
        name1, name2 = losowi_gracze[0]["name"], losowi_gracze[1]["name"]

        outsider_name = "Outsider"
        if outsiderzy:
            outsider_name = random.choice(outsiderzy).get("name", "Outsider")

        tekst = (
            f"Tylko jeden z graczy: {name1} oraz {name2} "
            f"ma postać: {outsider_name}"
        )

    else:
        if assigned_outsiderzy:
            outsider = random.choice(assigned_outsiderzy)
            outsider_client_id = outsider.get("client_id")
            kandydaci = [
                c
                for c in assigned_chars
                if c.get("client_id") and c.get("client_id") != outsider_client_id
            ]
            if not kandydaci:
                return "Brak wystarczającej liczby różnych graczy do losowania."

            druga_postac = random.choice(kandydaci)

            outsider["druga_postac"] = [outsider["name"], druga_postac["name"]]

            name1 = safe_player_name(outsider_client_id)
            name2 = safe_player_name(druga_postac.get("client_id"))

            names = [name1, name2]
            random.shuffle(names)

            tekst = (
                f"Tylko jeden z graczy: {names[0]} oraz {names[1]} "
                f"ma postać: {outsider['name']}"
            )
        else:
            tekst = "Żaden Outsider nie jest w grze."

    return tekst

def fun_detektyw(characters, players, drunk=False, poisoned=False):
    """
    Funkcja dla postaci 'Detektyw'.
    Informuje, że 1 z 2 graczy ma konkretną postać Miniona.
    """

    all_chars = [c for chars in characters.values() for c in chars]
    minionki = characters.get("Minionki", [])
    assigned_chars = [c for c in all_chars if c.get("client_id") in players]
    assigned_minionki = [c for c in minionki if c.get("client_id") in players]

    if len(players) < 2:
        return "Brak wystarczającej liczby graczy do losowania."

    def safe_player_name(client_id):
        if not client_id or client_id not in players:
            return "Nieznany"
        try:
            return players[client_id].get("name", "Nieznany")
        except KeyError:
            return "Nieznany"

    if assigned_minionki:
        minion = random.choice(assigned_minionki)
        minion_client_id = minion.get("client_id")
        kandydaci = [
            c
            for c in assigned_chars
            if c.get("client_id") and c.get("client_id") != minion_client_id
        ]
        if not kandydaci:
            return "Brak wystarczającej liczby różnych graczy do losowania."

        druga_postac = random.choice(kandydaci)
        minion["druga_postac"] = [minion["name"], druga_postac["name"]]

        name1 = safe_player_name(minion_client_id)
        name2 = safe_player_name(druga_postac.get("client_id"))
        names = [name1, name2]
        random.shuffle(names)

        return (
            f"Tylko jeden z graczy: {names[0]} oraz {names[1]} "
            f"ma postać: {minion['name']}"
        )

    wszyscy_gracze = list(players.get_all().values())
    losowi_gracze = random.sample(wszyscy_gracze, 2)
    name1, name2 = losowi_gracze[0]["name"], losowi_gracze[1]["name"]
    return (
        f"Żaden Minion nie jest w grze. "
        f"Przykładowi gracze: {name1} oraz {name2}."
    )

def fun_kucharz(characters, players, drunk=False, poisoned=False):
    """
    Funkcja dla postaci 'Kucharz'.
    Informuje, ile par złych postaci (Minionki lub Demon) siedzi obok siebie.
    Sąsiedztwo liczone jest po okręgu, więc pierwszy i ostatni gracz też sąsiadują.
    """

    if len(players) < 2:
        return "Brak wystarczającej liczby graczy do losowania."

    bad_roles = characters.get("Minionki", []) + characters.get("Demon", [])
    bad_client_ids = {
        char.get("client_id")
        for char in bad_roles
        if char.get("client_id") in players
    }

    if drunk or poisoned:
        max_pairs = (len(bad_client_ids) // 2) + 1
        return f"Liczba par złych postaci siedzących obok siebie: {random.randint(0, max_pairs)}."

    seated_players = []
    for client_id, player in players.get_all().items():
        seat = player.get("seat")
        if seat is None:
            continue

        seated_players.append({
            "client_id": client_id,
            "seat": seat,
            "is_bad": client_id in bad_client_ids,
        })

    if len(seated_players) < 2:
        return "Brak wystarczających danych o miejscach graczy."

    seated_players.sort(key=lambda player: player["seat"])

    bad_pairs = 0
    for index, current_player in enumerate(seated_players):
        next_player = seated_players[(index + 1) % len(seated_players)]
        if current_player["is_bad"] and next_player["is_bad"]:
            bad_pairs += 1

    return f"Liczba par złych postaci siedzących obok siebie: {bad_pairs}."

def fun_empata(characters, players, drunk=False, poisoned=False):
    """
    Funkcja dla postaci 'Empata'.
    Zwraca liczbę złych sąsiadów (Minionki + Demon), pomijając sąsiadów z executed=True.
    Sąsiedztwo liczone po okręgu według numeru miejsca.
    """
    all_players = players.get_all()
    if len(all_players) < 3:
        return "Brak wystarczającej liczby graczy do działania Empaty."

    if drunk or poisoned:
        return (
            "Liczba żyjących złych sąsiadów Empaty "
            f"(Minionki + Demon): {random.randint(0, 2)}."
        )

    empath_character = None
    for char in characters.get("Mieszkańcy", []):
        if char.get("name") == "Empata" and char.get("client_id") in all_players:
            empath_character = char
            break

    if not empath_character:
        return "Empata nie jest w tej grze."

    empath_client_id = empath_character.get("client_id")
    empath_player = all_players.get(empath_client_id)
    if not empath_player:
        return "Brak danych gracza Empaty."

    empath_seat = empath_player.get("seat")
    if empath_seat is None:
        return "Brak numeru miejsca dla Empaty."

    seated_players = []
    for client_id, player in all_players.items():
        seat = player.get("seat")
        if seat is None:
            continue
        seated_players.append(
            {
                "client_id": client_id,
                "seat": seat,
                "executed": bool(player.get("executed", False)),
            }
        )

    if len(seated_players) < 3:
        return "Brak wystarczających danych o miejscach graczy."

    seated_players.sort(key=lambda player: player["seat"])

    empath_index = None
    for index, player in enumerate(seated_players):
        if player["client_id"] == empath_client_id:
            empath_index = index
            break

    if empath_index is None:
        return "Nie znaleziono Empaty przy stole."

    left_neighbor = seated_players[(empath_index - 1) % len(seated_players)]
    right_neighbor = seated_players[(empath_index + 1) % len(seated_players)]

    evil_client_ids = {
        char.get("client_id")
        for char in (characters.get("Minionki", []) + characters.get("Demon", []))
        if char.get("client_id") in all_players
    }

    evil_neighbors = 0
    for neighbor in [left_neighbor, right_neighbor]:
        if neighbor["executed"]:
            continue
        if neighbor["client_id"] in evil_client_ids:
            evil_neighbors += 1

    return (
        "Liczba żyjących złych sąsiadów Empaty "
        f"(Minionki + Demon): {evil_neighbors}."
    )

def fun_jasnowidz(characters, players, drunk=False, poisoned=False, mode="day", day_number=1):
    """
    Funkcja dla postaci 'Jasnowidz'.
    Jasnowidz raz dziennie wybiera 2 graczy i dostaje odpowiedź,
    czy w tej parze znajduje się Demon (Imp).
    """

    _ = drunk
    _ = poisoned

    all_players = players.get_all()
    if not all_players:
        return "Brak graczy w bazie."

    jasnowidz_character = None
    for char in characters.get("Mieszkańcy", []):
        if char.get("name") == "Jasnowidz" and char.get("client_id") in all_players:
            jasnowidz_character = char
            break

    if not jasnowidz_character:
        return "Jasnowidz nie jest w tej grze."

    if mode != "day":
        return "Akcja Jasnowidza jest dostępna tylko w ciągu dnia."

    used_day = jasnowidz_character.get("jasnowidz_last_day_used")
    last_result = jasnowidz_character.get("jasnowidz_daily_result")

    if used_day == day_number:
        if last_result:
            return f"Dzisiejsza odpowiedź Jasnowidza: {last_result}"
        return "Dzisiaj wykorzystałeś już pytanie Jasnowidza."

    players_hint = ", ".join(
        player.get("name", "Nieznany")
        for _, player in sorted(all_players.items(), key=lambda item: item[1].get("seat") or 9999)
    )
    return (
        "Wybierz 2 dowolnych graczy, aby sprawdzić czy w tej parze jest Imp. "
        f"Dostępni gracze: {players_hint}."
    )

def fun_grabarz(characters, players, drunk=False, poisoned=False):
    return "Na razie nic."

def fun_mnich(characters, players, drunk=False, poisoned=False):
    return "Na razie nic."

def fun_krukopiek(characters, players, drunk=False, poisoned=False):
    return "Na razie nic."

def fun_dziewica(characters, players, drunk=False, poisoned=False):
    return "Na razie nic."

def fun_zabojca(characters, players, drunk=False, poisoned=False):
    return "Na razie nic."

def fun_zolnierz(characters, players, drunk=False, poisoned=False):
    return "Na razie nic."

def fun_burmistrz(characters, players, drunk=False, poisoned=False):
    return "Na razie nic."

def fun_lokaj(characters, players, drunk=False, poisoned=False):
    return "Na razie nic."

def fun_pijak(characters, players, drunk=False, poisoned=False):
    return "Na razie nic."

def fun_samotnik(characters, players, drunk=False, poisoned=False):
    return "Na razie nic."

def fun_swiety(characters, players, drunk=False, poisoned=False):
    return "Na razie nic."

def fun_truciciel(characters, players, drunk=False, poisoned=False, mode="day", day_number=1):
    """
    Funkcja statusu Truciciela.
    Truciciel wybiera cel w dzień, a zatrucie staje się aktywne dopiero kolejnego dnia.
    """

    _ = drunk
    _ = poisoned

    all_players = players.get_all()
    if not all_players:
        return "Brak graczy w bazie."

    truciciel_character = None
    for char in characters.get("Minionki", []):
        if char.get("name") == "Truciciel" and char.get("client_id") in all_players:
            truciciel_character = char
            break

    if not truciciel_character:
        return "Truciciel nie jest w tej grze."

    poison_targets_by_day = truciciel_character.get("truciciel_poison_targets_by_day", {})
    active_target_id = poison_targets_by_day.get(str(day_number))
    next_target_id = poison_targets_by_day.get(str(day_number + 1))

    def target_name(client_id):
        if not client_id:
            return "brak"
        return all_players.get(client_id, {}).get("name", "Nieznany")

    status_lines = []

    if mode == "day":
        if truciciel_character.get("truciciel_last_day_used") == day_number:
            status_lines.append(
                f"Dzisiejszy wybór zapisany. Cel na kolejny dzień: {target_name(next_target_id)}."
            )
        else:
            status_lines.append("Wybierz w tym dniu cel zatrucia.")

    if active_target_id:
        status_lines.append(
            f"Aktywne zatrucie (dzień {day_number}): {target_name(active_target_id)}."
        )
    else:
        status_lines.append(f"Aktywne zatrucie (dzień {day_number}): brak.")

    return "\n".join(status_lines)

def fun_szpieg(characters, players, drunk=False, poisoned=False):
    return "Na razie nic."

def fun_scarlet(characters, players, drunk=False, poisoned=False):
    return "Na razie nic."

def fun_baron(characters, players, drunk=False, poisoned=False):
    return "Na razie nic."

def fun_imp(characters, players, drunk=False, poisoned=False, mode="day"):
    """
    Funkcja dla postaci 'Imp'.
    Na start zwraca stałe informacje:
    - lista graczy będących Minionkami,
    - lista 3 postaci przygotowanych dla Impa (jeśli dostępne).
    W nocy dodatkowo pokazuje listę wszystkich graczy.
    """

    _ = drunk
    _ = poisoned

    all_players = players.get_all()
    if not all_players:
        return "Brak graczy w bazie."

    imp_character = None
    for char in characters.get("Demon", []):
        if char.get("name") == "Imp" and char.get("client_id") in all_players:
            imp_character = char
            break

    if not imp_character:
        return "Imp nie jest w tej grze."

    minion_names = []
    for minion in characters.get("Minionki", []):
        minion_client_id = minion.get("client_id")
        if minion_client_id in all_players:
            minion_names.append(all_players[minion_client_id].get("name", "Nieznany"))

    if minion_names:
        minions_info = ", ".join(minion_names)
    else:
        minions_info = "Brak Minionów w tej rozgrywce."

    imp_extra_roles = imp_character.get("druga_postac")
    if isinstance(imp_extra_roles, list) and imp_extra_roles:
        extra_roles = imp_extra_roles[:3]
    else:
        unassigned_roles = []
        for group_chars in characters.values():
            for char in group_chars:
                if char.get("client_id") is None:
                    unassigned_roles.append(char.get("name", "Nieznana postać"))

        if len(unassigned_roles) >= 3:
            extra_roles = random.sample(unassigned_roles, 3)
        else:
            extra_roles = unassigned_roles

    if extra_roles:
        extra_roles_info = ", ".join(extra_roles)
    else:
        extra_roles_info = "Brak dostępnych postaci do podania."

    status_lines = [
        f"Minionki w grze (Twoi sojusznicy): {minions_info}.",
        f"Tych trzech mieszkańców nie bierze udziału w grze (możesz udawać, że jesteś jednym z nich): {extra_roles_info}.",
    ]

    if mode == "night":
        players_info = []
        for client_id, player in sorted(all_players.items(), key=lambda item: item[1].get("seat") or 9999):
            executed_label = "wyeliminowany" if player.get("executed", False) else "żywy"
            players_info.append(f"{player.get('name', 'Nieznany')} ({executed_label})")
        status_lines.append("Wszyscy gracze: " + ", ".join(players_info) + ".")

    return "\n".join(status_lines)
