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

## Jak to działa krok po kroku (przepływ tam i z powrotem)
1. Tak samo jak w zad. 3, ale `agent._find_path` wywołuje `astar_find_path(...)`.
2. **Funkcja priorytetu** `f(n) = g(n) + h(n)`:
   - `g(n)` = realny dotychczasowy koszt = suma `TERRAIN_COSTS` (piasek 2.0 / skała 6.0) + `TURN_COST` 0.5,
   - `h(n)` = heurystyka = **odległość Manhattan** do celu.
3. **OPEN = kopiec priorytetowy** (`heapq`): zawsze rozwijamy węzeł o najmniejszym `f`.
4. A* preferuje tanie pola (piasek) i **omija drogie skały**, więc trasa jest tańsza energetycznie
   niż „na ślepo” u BFS.
5. Wynik (`decyzja/sciezka.txt`) pokazuje najtańszą ścieżkę, jej koszt energii oraz **porównanie
   liczby rozwiniętych węzłów A\* vs BFS** (A\* rozwija ich mniej).
6. Powrót do bazy/stacji liczony tym samym A* — dlatego łazik żyje dłużej niż na BFS (zad. 3).

## Pytania prowadzącego (Q&A do obrony)
- **Czym A\* różni się od BFS?** BFS ignoruje koszty (graf bez wag). A\* używa kosztu `g` i
  heurystyki `h`, więc znajduje **najtańszą** trasę, a nie tylko najkrótszą w krokach.
- **Dlaczego heurystyka Manhattan jest dopuszczalna (admissible)?** Bo na kracie z ruchem
  w 4 kierunkach nigdy nie **przeszacowuje** realnego kosztu — dzięki temu A\* jest optymalny.
- **Co, gdyby `h = 0`?** A\* degeneruje się do **algorytmu Dijkstry** (też optymalny, ale wolniejszy).
- **Co, gdyby `h` przeszacowywała?** A\* przestaje być optymalny — może znaleźć droższą ścieżkę.
- **Po co kopiec priorytetowy?** Żeby w `O(log n)` zawsze pobierać węzeł o najmniejszym `f`.
- **Dlaczego A\* rozwija mniej węzłów niż BFS?** Heurystyka „kieruje” przeszukiwanie ku celowi,
  zamiast rozlewać się równomiernie we wszystkie strony.
