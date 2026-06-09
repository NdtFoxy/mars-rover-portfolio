# Zadania projektowe — materiały do obrony

Każdy folder `zadanie_N_*` jest **samodzielny** i zawiera:
- **PDF** — treść zadania od prowadzącego,
- **README.md** — wymagania z PDF + jak je spełniliśmy,
- plik z **realną implementacją algorytmu** (`bfs.py`, `astar.py`, `drzewo.py`,
  `siec.py` albo `genetyczny.py`),
- **uruchom.py** — szybka demonstracja używająca tej samej implementacji co serwer,
- **zbior/** — dane wejściowe / **zbiór uczący**,
- **decyzja/** — **wynik / decyzja** algorytmu.

`app/core/agent.py` importuje algorytmy bezpośrednio z tych folderów. Dzięki temu
kod pokazany przy obronie jest dokładnie kodem używanym przez działającego łazika.
CNN jest trenowana tylko dla zadania 6; w pozostałych trybach bazową decyzję
`GO_TO_CHARGE` / `CONTINUE_MINING` podejmuje szybkie drzewo decyzyjne.

| # | Folder | Algorytm | zbiór | decyzja |
|---|--------|----------|-------|---------|
| 3 | `zadanie_3_BFS` | Breadth-First Search | mapa | ścieżka + rozwinięte węzły |
| 4 | `zadanie_4_Astar` | A* (koszt + heurystyka) | mapa + koszty kafli | najtańsza ścieżka (A* vs BFS) |
| 5 | `zadanie_5_DrzewoDecyzyjne` | Drzewo decyzyjne (ID3) | `rover_training_data.csv` (≥200, 8 atr.) | `drzewo.png` + `reguly.txt` |
| 6 | `zadanie_6_SiecNeuronowa` | CNN + MLP | zbiór ≥1000/klasę + zdjęcia UE5 | raport decyzji sieci |
| 7 | `zadanie_7_AlgorytmGenetyczny` | Algorytm genetyczny (plecak) | instancja (waga/objętość/wartość) | wybór GA + weryfikacja DP |

## Szybki pokaz dowolnego zadania
```sh
cd backend
python3 zadania/zadanie_3_BFS/uruchom.py          # i analogicznie 4,5,6,7
```
Wyniki trafiają do `zbior/` i `decyzja/` danego folderu (gotowe do pokazania).

## Wersja „na żywo” (symulacja + Unreal Engine)
```sh
python3 navigate.py    # wybór zadania
python3 run.py         # uruchomienie + hot-reload (Alt+R)
```
