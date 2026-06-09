# Zadanie projektowe 3 — Niepoinformowane strategie przeszukiwania (BFS)

**PDF:** `route-planning (1).pdf`

## Wymagania (z PDF)
1. Zastosowanie strategii przeszukiwania przestrzeni stanów do planowania ruchu agenta na kracie.
2. Wykorzystanie „Schematu procedury przeszukiwania grafu stanów”.
3. Implementacja strategii **Breadth-First Search**.
4. Agent dysponuje akcjami: ruch do przodu, obrót w lewo, obrót w prawo.

## Realizacja
- Algorytm: `bfs.py` → `bfs_find_path` (kolejka FIFO, stan = `(x, y, kierunek)`, akcje `MOVE_FORWARD / TURN_LEFT / TURN_RIGHT`, bez kosztu i heurystyki).
- `app/core/agent.py` importuje tę funkcję bezpośrednio i używa jej, gdy aktywne jest zadanie 3.
- Mapa generowana przez `Environment` (piasek / skała / krater).

## Pliki
- `zbior/mapa.txt` — dane wejściowe (mapa + start/cel)
- `decyzja/sciezka.txt` — wynik: najkrótsza ścieżka (akcje) + liczba rozwiniętych węzłów

## Uruchomienie
```sh
python3 uruchom.py
```
