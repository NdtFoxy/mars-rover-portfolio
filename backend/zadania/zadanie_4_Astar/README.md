# Zadanie projektowe 4 — Poinformowane strategie przeszukiwania (A*)

**PDF:** `route-planning-2.pdf`

## Wymagania (z PDF)
1. Poinformowane przeszukiwanie przestrzeni stanów do planowania ruchu agenta na kracie.
2. „Schemat procedury przeszukiwania grafu stanów z uwzględnieniem kosztu”.
3. Implementacja **A\*** — funkcja priorytetu = koszt **g(n)** + heurystyka **h(n)**.
4. Akcje agenta: ruch do przodu, obrót w lewo, obrót w prawo.
5. **Zróżnicowany koszt** wjazdu na pola różnych typów (np. piasek vs skała).

## Realizacja
- Algorytm: `astar.py` → `astar_find_path` (kopiec priorytetowy, `f = g + h`, `h` = odległość Manhattan).
- Koszty kafli: `TERRAIN_COSTS` (piasek `2.0`, skała `6.0`), obrót `0.5`.
- W wyniku pokazane jest porównanie liczby rozwiniętych węzłów A\* vs BFS (A\* jest efektywniejszy).
- `app/core/agent.py` importuje tę funkcję bezpośrednio i używa jej w trybach innych niż zadanie 3.

## Pliki
- `zbior/mapa.txt` — mapa + koszty kafli + start/cel
- `decyzja/sciezka.txt` — najtańsza ścieżka, koszt energetyczny, porównanie z BFS

## Uruchomienie
```sh
python3 uruchom.py
```
