from utils import (
    fun_praczka,
    fun_bibliotekarka,
    fun_detektyw,
    fun_kucharz,
    fun_empata,
    fun_jasnowidz,
    fun_grabarz,
    fun_mnich,
    fun_krukopiek,
    fun_dziewica,
    fun_zabojca,
    fun_zolnierz,
    fun_burmistrz,
    fun_lokaj,
    fun_pijak,
    fun_samotnik,
    fun_swiety,
    fun_truciciel,
    fun_szpieg,
    fun_scarlet,
    fun_baron,
    fun_imp
)


db_characters = {
    "Mieszkańcy": [
        {
            "client_id": None, 
            "name": "Praczka", 
            "file": "praczka.png", 
            "route": "praczka", 
            "player_status": fun_praczka, 
            "player_info": "Na początku wiesz, że 1 z 2 graczy jest konkretnym mieszczaninem.\nPraczka dowiaduje się, że konkretny mieszczanin jest w grze, ale nie kto go gra."
        },
        {
            "client_id": None, 
            "name": "Bibliotekarka", 
            "file": "bibliotekarka.png", 
            "route": "bibliotekarka", 
            "player_status": fun_bibliotekarka, 
            "player_info": "Na początku wiesz, że 1 z 2 graczy jest konkretnym Outsiderem (lub że żaden nie jest w grze). Bibliotekarka dowiaduje się, że konkretny Outsider jest w grze, ale nie kto go gra."
        },
        {
            "client_id": None, 
            "name": "Detektyw", 
            "file": "detektyw.png", 
            "route": "detektyw", 
            "player_status": fun_detektyw, 
            "player_info": "Na początku wiesz, że 1 z 2 graczy jest konkretnym Minionem. Detektyw dowiaduje się, że konkretny Minion jest w grze, ale nie kto go gra."
        },
        {
            "client_id": None, 
            "name": "Kucharz", 
            "file": "kucharz.png", 
            "route": "kucharz", 
            "player_status": fun_kucharz, 
            "player_info": "Na początku wiesz, ile par złych graczy siedzi obok siebie. Kucharz wie, czy źli gracze siedzą obok siebie."
        },
        {
            "client_id": None, 
            "name": "Empata", 
            "file": "empata.png", 
            "route": "empata", 
            "player_status": fun_empata, 
            "player_info": "Po każdej nocy Empata dowiaduje się, ilu z jego dwóch żyjących sąsiadów jest złych. Empata uczy się, czy sąsiadujący z nim gracze są dobrzy czy źli."
        },
        {
            "client_id": None, 
            "name": "Jasnowidz", 
            "file": "jasnowidz.png", 
            "route": "jasnowidz", 
            "player_status": fun_jasnowidz, 
            "player_info": "Po każdej nocy wybierz 2 graczy: dowiadujesz się, czy którykolwiek z nich jest Demonem. Jasnowidz dowiaduje się, czy którykolwiek z dwóch graczy jest Demonem."    
        },
        # {"client_id": None, "name": "Grabarz", "file": "grabarz.png", "route": "grabarz", "player_status": fun_grabarz, "player_info": "TBD"},
        # {"client_id": None, "name": "Mnich", "file": "mnich.png", "route": "mnich", "player_status": fun_mnich, "player_info": "TBD"},
        # {"client_id": None, "name": "Strażnik Kruka", "file": "krukopiek.png", "route": "krukopiek", "player_status": fun_krukopiek, "player_info": "TBD"},
        # {"client_id": None, "name": "Dziewica", "file": "dziewica.png", "route": "dziewica", "player_status": fun_dziewica, "player_info": "TBD"},
        # {"client_id": None, "name": "Zabójca", "file": "zabojca.png", "route": "zabojca", "player_status": fun_zabojca, "player_info": "TBD"},
        # {"client_id": None, "name": "Żołnierz", "file": "zolnierz.png", "route": "zolnierz", "player_status": fun_zolnierz, "player_info": "TBD"},
        # {"client_id": None, "name": "Burmistrz", "file": "burmistrz.png", "route": "burmistrz", "player_status": fun_burmistrz, "player_info": "TBD"},
    ],
    "Outsiderzy": [
        # {"client_id": None, "name": "Lokaj", "file": "lokaj.png", "route": "lokaj", "player_status": fun_lokaj, "player_info": "TBD"},
        {
            "client_id": None, 
            "name": "Pijak", 
            "file": "pijak.png", 
            "route": "pijak", 
            "player_status": fun_pijak, 
            "player_info": "Nie wiesz, że jesteś Pijakiem. Myślisz, że jesteś postacią z grupy Townsfolk, ale nią nie jesteś."
        },
        # {"client_id": None, "name": "Samotnik", "file": "samotnik.png", "route": "samotnik", "player_status": fun_samotnik, "player_info": "TBD"},
        # {"client_id": None, "name": "Święty", "file": "swiety.png", "route": "swiety", "player_status": fun_swiety, "player_info": "TBD"},
    ],
    "Minionki": [
        {
            "client_id": None, 
            "name": "Truciciel", 
            "file": "truciciel.png", 
            "route": "truciciel", 
            "player_status": fun_truciciel, 
            "player_info": "Każdego dnia wybierz gracza: tej nocy i następnego dnia ten gracz jest zatruty. Truciciel potajemnie zakłóca działanie zdolności postaci."
        },
        # {"client_id": None, "name": "Szpieg", "file": "szpieg.png", "route": "szpieg", "player_status": fun_szpieg, "player_info": "TBD"},
        # {"client_id": None, "name": "Scarlet Woman", "file": "scarlet.png", "route": "scarlet", "player_status": fun_scarlet, "player_info": "TBD"},
        # {"client_id": None, "name": "Baron", "file": "baron.png", "route": "baron", "player_status": fun_baron, "player_info": "TBD"},
    ],
    "Demon": [
        {
            "client_id": None, 
            "name": "Imp", 
            "file": "imp.png", 
            "route": "imp", 
            "player_status": fun_imp, 
            "player_info": "Każdej nocy, wybierz gracza: ten gracz umiera. Jeśli w ten sposób zabijesz samego siebie, jeden z Minionów staje się Impem. Imp zabija jednego gracza każdej nocy i może „stworzyć kopię samego siebie”… za straszną cenę."
        },
    ]
}

trouble_brewing_setup = [
    {"gracze": 5,  "Mieszkańcy": 3, "Outsiderzy": 0, "Minionki": 1, "Demon": 1},
    {"gracze": 6,  "Mieszkańcy": 3, "Outsiderzy": 1, "Minionki": 1, "Demon": 1},
    {"gracze": 7,  "Mieszkańcy": 5, "Outsiderzy": 0, "Minionki": 1, "Demon": 1},
    {"gracze": 8,  "Mieszkańcy": 5, "Outsiderzy": 1, "Minionki": 1, "Demon": 1},
    {"gracze": 9,  "Mieszkańcy": 5, "Outsiderzy": 2, "Minionki": 1, "Demon": 1},
    {"gracze": 10, "Mieszkańcy": 7, "Outsiderzy": 0, "Minionki": 2, "Demon": 1},
    {"gracze": 11, "Mieszkańcy": 7, "Outsiderzy": 1, "Minionki": 2, "Demon": 1},
    {"gracze": 12, "Mieszkańcy": 7, "Outsiderzy": 2, "Minionki": 2, "Demon": 1},
    {"gracze": 13, "Mieszkańcy": 9, "Outsiderzy": 0, "Minionki": 3, "Demon": 1},
    {"gracze": 14, "Mieszkańcy": 9, "Outsiderzy": 1, "Minionki": 3, "Demon": 1},
    {"gracze": 15, "Mieszkańcy": 9, "Outsiderzy": 2, "Minionki": 3, "Demon": 1},
]