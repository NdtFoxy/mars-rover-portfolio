# Backend — Autonomiczny Łazik Marsjański (przegląd techniczny)

Ten dokument opisuje, **jak całość działa** od strony backendu (Python / FastAPI),
jak dane krążą między serwerem a Unreal Engine 5 oraz zawiera **pytania prowadzącego
z odpowiedziami** do obrony.

---

## 1. Architektura ogólna

```
┌─────────────────┐   HTTP / REST (JSON)   ┌──────────────────────────┐
│   UNREAL 5      │  ───────────────────►  │   FastAPI  (app/api.py)  │
│  (wizualizacja) │   GET /state           │                          │
│  „ciało+oczy”   │  POST /step            │   ┌──────────────────┐   │
│                 │  ◄───────────────────  │   │  Agent (mózg)    │   │
└─────────────────┘   stan świata (JSON)   │   │  Environment     │   │
                                           │   │  Shop / Mission  │   │
                                           │   └──────────────────┘   │
                                           └──────────────────────────┘
```

- **Backend** = cała logika: ruch, fizyka energii, decyzje AI, ekonomia, generacja mapy.
- **UE5** = tylko wizualizacja (renderuje to, co przyśle backend) i wysyła sygnał kroku.
- Komunikacja jest **bezstanowa po HTTP**: UE5 co 1–2 s woła `POST /step`, dostaje nowy stan.

---

## 2. Przepływ jednego kroku (`POST /step`)

```
1. Agent MYŚLI        -> follow_plan_or_search()  (BFS/A* + decyzja drzewo/CNN)
2. Agent DZIAŁA       -> interact_and_recharge()   (kopanie / ładowanie / baza+sklep)
3. ŚWIAT się zmienia  -> update_time_and_weather()  (czas, pogoda, regeneracja)
4. Stan -> JSON       -> get_current_state()        (odsyłka do UE5)
```

To jest serce symulacji — każda klatka gry to powtórzenie tych 4 kroków.

---

## 3. Trzy niezależne warstwy (klucz do zrozumienia projektu)

| Warstwa | Co robi | Od czego zależy |
|---|---|---|
| **TRASA** | jak dojść do celu | zadanie: **BFS** (zad. 3) / **A\*** (zad. 4–7) |
| **DECYZJA** | kopać czy ładować | klasyfikator: **CNN** (zad. 6) / **drzewo ID3** (reszta) |
| **EKONOMIA** | co kopać, sprzedaż, sklep | **wspólna** dla wszystkich zadań (plecak GA) |

Dlatego zadania 4,5,6,7 dają podobne wyniki — różnią się tylko warstwą trasy/decyzji,
a silnik energii i ekonomii jest ten sam. Jedyna duża różnica to **BFS (zad. 3) vs A\* (reszta)**.

---

## 4. Zadania projektowe 3–7

| # | Algorytm | Plik | Wejście (`zbior/`) | Wynik (`decyzja/`) |
|---|----------|------|--------------------|--------------------|
| 3 | BFS (niepoinformowane) | `zadania/zadanie_3_BFS/bfs.py` | mapa | ścieżka + rozwinięte węzły |
| 4 | A\* (poinformowane) | `zadania/zadanie_4_Astar/astar.py` | mapa + koszty | najtańsza ścieżka (A\* vs BFS) |
| 5 | Drzewo decyzyjne ID3 | `zadania/zadanie_5_.../drzewo.py` | 300 przykładów, 8 atrybutów | `drzewo.png` + reguły |
| 6 | Sieć neuronowa CNN+MLP | `zadania/zadanie_6_.../siec.py` | ≥1000/klasę + zdjęcia UE5 | raport sieci |
| 7 | Algorytm genetyczny | `zadania/zadanie_7_.../genetyczny.py` | instancja plecaka | wybór GA + walidacja DP |

`app/core/agent.py` importuje algorytmy **bezpośrednio z tych folderów** — kod pokazany
przy obronie jest dokładnie kodem działającego łazika (brak dwóch wersji).

---

## 5. Mózg łazika: drzewo vs CNN

- **Drzewo decyzyjne (zad. 5)** jest uczone ZAWSZE przy starcie serwera i służy jako bazowy
  mózg decyzji `GO_TO_CHARGE` / `CONTINUE_MINING` we wszystkich zadaniach poza 6.
- **Sieć CNN+MLP (zad. 6)** jest uczona LENIWIE — tylko gdy aktywne jest zadanie 6.
- Oba modele uczone są na tych samych 7 cechach telemetrii, więc decydują niemal identycznie.

---

## 6. Współczynniki trudności energetycznej

| Stała | Wartość | Źródło |
|---|---|---|
| koszt ruchu po piasku | 2.0 | `astar.py: TERRAIN_COSTS[0]` |
| koszt ruchu po skale | 6.0 | `astar.py: TERRAIN_COSTS[1]` |
| koszt obrotu | 0.5 | `astar.py: TURN_COST` |
| mnożnik silnika | 1.0 | `agent.py: motor_efficiency` |
| zapas energii stacji | 500.0 | `environment.py: _regenerate_chargers` |
| tempo ładowania | 25/krok | `agent.py: charge_amount` |

Trudność zależna od kroków: `time_of_day = step_counter * 0.25` (dzień/noc) i zmiana pogody co 8 kroków.
Szczegóły i pomiary: `../survival_comparison.txt`.

---

## 7. Jak uruchomić

**Pojedyncze zadanie (demonstracja do obrony, bez UE5):**
```sh
python3 zadania/zadanie_3_BFS/uruchom.py      # i analogicznie 4,5,6,7
```
Wynik trafia do `zbior/` i `decyzja/` danego zadania.

**Wersja „na żywo” (serwer + UE5):**
```sh
python3 navigate.py    # wybór aktywnego zadania (zapis do mission_config.json)
python3 run.py         # serwer + hot-reload (Alt+R przeładowuje zadanie bez restartu)
```
Serwer: http://localhost:8000/docs (Swagger). Testy: `python3 test_rover.py`.

---

## 8. Pytania prowadzącego — ogólne (Q&A)

**P: Dlaczego logika jest w Pythonie, a nie w UE5?**
O: Rozdzielenie odpowiedzialności — backend liczy „mózg”, UE5 tylko renderuje. Łatwiej testować
logikę osobno (mamy `test_rover.py`) i podmieniać klienta.

**P: Jak UE5 komunikuje się z backendem?**
O: Asynchronicznie po HTTP/REST. UE5 woła `GET /state` i `POST /step`, dostaje JSON (Pydantic).

**P: Dlaczego zadania 4–7 dają te same liczby przeżywalności?**
O: Bo dzielą tę samą warstwę trasy (A\*) i ekonomii; różni je tylko klasyfikator (CNN vs drzewo),
który decyduje niemal identycznie. Realnie różni się tylko zad. 3 (BFS).

**P: Czy ten sam kod jest na obronie i w grze?**
O: Tak — `agent.py` importuje algorytmy z folderów `zadania/`, więc `uruchom.py` i serwer
używają dokładnie tych samych funkcji.

**P: Co się dzieje, gdy bateria spadnie do zera?**
O: Permadeath — status `DEAD`, łazik przestaje działać (mechanika w `agent._check_death`).

**P: Czym jest „pętla ekonomiczna”?**
O: Wydobycie (plecak GA) → sprzedaż na bazie → zakup ulepszeń w sklepie → większy plecak →
trudniejszy problem plecakowy. Wszystko spięte w jeden obieg.

---

Szczegóły kodu backendu: `app/README.md`. Materiały per zadanie: `zadania/README.md` oraz README w folderach `zadania/zadanie_*`.
